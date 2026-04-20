#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Ansible module for SDDC Manager workload domain creation."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vcf_sddc_domain
short_description: Create or validate a VCF workload domain
description:
  - Creates a VI workload domain via SDDC Manager REST API.
  - Optionally validates the domain spec before creation.
  - Polls the resulting task until completion.
options:
  sddc_hostname:
    description: SDDC Manager hostname or IP.
    required: true
    type: str
  username:
    description: SDDC Manager username.
    required: true
    type: str
  password:
    description: SDDC Manager password.
    required: true
    type: str
    no_log: true
  state:
    description: >
      C(present) creates the workload domain.
      C(validated) runs pre-flight validation only.
    required: true
    type: str
    choices: [present, validated]
  domain_spec:
    description: >
      Workload domain specification as a dict or path to a JSON file.
    required: true
    type: raw
  timeout:
    description: Maximum wait time in seconds.
    required: false
    type: int
    default: 5400
  poll_interval:
    description: Seconds between status checks.
    required: false
    type: int
    default: 30
  validate_certs:
    description: Whether to validate SSL certificates.
    required: false
    type: bool
    default: false
"""

import json
import os
import time

from ansible.module_utils.basic import AnsibleModule

try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
except ImportError:
    from urllib2 import Request, urlopen, URLError, HTTPError


def make_ssl_context(validate_certs):
    import ssl

    if validate_certs:
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def get_bearer_token(base_url, username, password, validate_certs):
    """Authenticate and return a bearer token."""
    url = f"{base_url}/v1/tokens"
    payload = json.dumps({"username": username, "password": password}).encode()
    req = Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    ctx = make_ssl_context(validate_certs)
    resp = urlopen(req, context=ctx)
    data = json.loads(resp.read().decode())
    return data["accessToken"]


def api_request(url, method, token, data=None, validate_certs=False):
    """Make an authenticated API request to SDDC Manager."""
    payload = json.dumps(data).encode() if data else None
    req = Request(url, data=payload, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    ctx = make_ssl_context(validate_certs)
    resp = urlopen(req, context=ctx)
    return json.loads(resp.read().decode())


def poll_task(base_url, token, task_id, timeout, poll_interval, validate_certs, module=None):
    """Poll a task until it reaches a terminal state."""
    start_time = time.time()
    last_status = None
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            return None, f"Task {task_id} timed out after {timeout}s"

        task = api_request(
            f"{base_url}/v1/tasks/{task_id}",
            "GET",
            token,
            validate_certs=validate_certs,
        )
        status = task.get("status", "UNKNOWN")
        progress = task.get("progressPercent", 0)

        # Print progress every status change or every 2 minutes
        if status != last_status or elapsed % 120 < poll_interval:
            msg = f"Task {task_id}: {status} ({progress}%) — elapsed {int(elapsed)}s"
            if module:
                module.debug(msg)
            last_status = status

        if status == "SUCCESSFUL":
            return task, None
        elif status in ("FAILED", "CANCELLED"):
            return task, f"Task {task_id} {status}"

        time.sleep(poll_interval)


def run_module():
    module_args = dict(
        sddc_hostname=dict(type="str", required=True),
        username=dict(type="str", required=True),
        password=dict(type="str", required=True, no_log=True),
        state=dict(type="str", required=True, choices=["present", "validated"]),
        domain_spec=dict(type="raw", required=True),
        timeout=dict(type="int", required=False, default=5400),
        poll_interval=dict(type="int", required=False, default=30),
        validate_certs=dict(type="bool", required=False, default=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(changed=False, msg="Check mode — no action taken")

    base_url = f"https://{module.params['sddc_hostname']}"
    validate_certs = module.params["validate_certs"]
    timeout = module.params["timeout"]
    poll_interval = module.params["poll_interval"]

    # Load domain spec
    domain_spec = module.params["domain_spec"]
    if isinstance(domain_spec, str) and os.path.isfile(domain_spec):
        try:
            with open(domain_spec) as f:
                domain_spec = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            module.fail_json(msg=f"Failed to load domain spec file: {e}")

    if not isinstance(domain_spec, dict):
        module.fail_json(msg="domain_spec must be a dict or path to a JSON file")

    try:
        token = get_bearer_token(
            base_url,
            module.params["username"],
            module.params["password"],
            validate_certs,
        )
    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass
        module.fail_json(
            msg=f"Failed to authenticate: {e}",
            status_code=e.code,
            response_body=body,
        )
    except URLError as e:
        module.fail_json(msg=f"Failed to authenticate: {e}")

    try:
        if module.params["state"] == "validated":
            result = api_request(
                f"{base_url}/v1/domains/validations",
                "POST",
                token,
                data=domain_spec,
                validate_certs=validate_certs,
            )
            module.exit_json(
                changed=False,
                validation_id=result.get("id"),
                result=result,
            )

        elif module.params["state"] == "present":
            result = api_request(
                f"{base_url}/v1/domains",
                "POST",
                token,
                data=domain_spec,
                validate_certs=validate_certs,
            )
            task_id = result.get("id")
            task, error = poll_task(
                base_url, token, task_id, timeout, poll_interval, validate_certs, module
            )
            if error:
                module.fail_json(msg=error, task=task)
            module.exit_json(
                changed=True,
                task_id=task_id,
                domain_id=result.get("id"),
                status="SUCCESSFUL",
                task=task,
            )

    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass
        module.fail_json(
            msg=f"SDDC Manager API error: {e}",
            status_code=e.code,
            response_body=body,
        )
    except URLError as e:
        module.fail_json(msg=f"SDDC Manager API error: {e}")


def main():
    run_module()


if __name__ == "__main__":
    main()

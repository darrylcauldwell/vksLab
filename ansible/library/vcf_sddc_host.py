#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Ansible module for SDDC Manager host commissioning."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vcf_sddc_host
short_description: Commission or decommission hosts in SDDC Manager
description:
  - Commissions ESXi hosts into the SDDC Manager free pool.
  - Decommissions hosts from the free pool.
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
      C(commissioned) adds hosts to the free pool.
      C(absent) decommissions hosts.
    required: true
    type: str
    choices: [commissioned, absent]
  hosts:
    description: >
      List of host specs to commission. Each item needs fqdn, username,
      password, networkPoolName, and storageType.
    required: true
    type: list
    elements: dict
  timeout:
    description: Maximum wait time in seconds.
    required: false
    type: int
    default: 3600
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


def poll_task(base_url, token, task_id, timeout, poll_interval, validate_certs):
    """Poll a task until it reaches a terminal state."""
    start_time = time.time()
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
        state=dict(type="str", required=True, choices=["commissioned", "absent"]),
        hosts=dict(type="list", required=True, elements="dict"),
        timeout=dict(type="int", required=False, default=3600),
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

    try:
        token = get_bearer_token(
            base_url,
            module.params["username"],
            module.params["password"],
            validate_certs,
        )
    except (URLError, HTTPError) as e:
        module.fail_json(msg=f"Failed to authenticate: {e}")

    try:
        if module.params["state"] == "commissioned":
            result = api_request(
                f"{base_url}/v1/hosts",
                "POST",
                token,
                data=module.params["hosts"],
                validate_certs=validate_certs,
            )
            task_id = result.get("id")
            task, error = poll_task(
                base_url, token, task_id, timeout, poll_interval, validate_certs
            )
            if error:
                module.fail_json(msg=error, task=task)
            module.exit_json(
                changed=True,
                task_id=task_id,
                status="SUCCESSFUL",
                task=task,
            )

        elif module.params["state"] == "absent":
            # Decommission each host by FQDN
            for host_spec in module.params["hosts"]:
                fqdn = host_spec.get("fqdn", "")
                # Look up host ID by FQDN
                hosts_resp = api_request(
                    f"{base_url}/v1/hosts",
                    "GET",
                    token,
                    validate_certs=validate_certs,
                )
                host_id = None
                for h in hosts_resp.get("elements", []):
                    if h.get("fqdn") == fqdn:
                        host_id = h.get("id")
                        break
                if host_id:
                    api_request(
                        f"{base_url}/v1/hosts/{host_id}",
                        "DELETE",
                        token,
                        validate_certs=validate_certs,
                    )
            module.exit_json(changed=True, msg="Hosts decommissioned")

    except (URLError, HTTPError) as e:
        module.fail_json(msg=f"SDDC Manager API error: {e}")


def main():
    run_module()


if __name__ == "__main__":
    main()

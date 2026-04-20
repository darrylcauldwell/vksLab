#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Ansible module for polling SDDC Manager task status."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vcf_sddc_task
short_description: Poll an SDDC Manager task until completion
description:
  - Polls an SDDC Manager async task by ID until it reaches a terminal state.
  - Returns the final task status and any sub-task details.
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
  task_id:
    description: The SDDC Manager task ID to poll.
    required: true
    type: str
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


def get_bearer_token(base_url, username, password, validate_certs):
    """Authenticate and return a bearer token."""
    url = f"{base_url}/v1/tokens"
    payload = json.dumps({"username": username, "password": password}).encode()
    req = Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    import ssl

    ctx = None if validate_certs else ssl.create_default_context()
    if not validate_certs:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    resp = urlopen(req, context=ctx)
    data = json.loads(resp.read().decode())
    return data["accessToken"]


def get_task_status(base_url, token, task_id, validate_certs):
    """Get current task status."""
    url = f"{base_url}/v1/tasks/{task_id}"
    req = Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    import ssl

    ctx = None if validate_certs else ssl.create_default_context()
    if not validate_certs:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    resp = urlopen(req, context=ctx)
    return json.loads(resp.read().decode())


def run_module():
    module_args = dict(
        sddc_hostname=dict(type="str", required=True),
        username=dict(type="str", required=True),
        password=dict(type="str", required=True, no_log=True),
        task_id=dict(type="str", required=True),
        timeout=dict(type="int", required=False, default=3600),
        poll_interval=dict(type="int", required=False, default=30),
        validate_certs=dict(type="bool", required=False, default=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(changed=False, msg="Check mode — no action taken")

    base_url = f"https://{module.params['sddc_hostname']}"
    timeout = module.params["timeout"]
    poll_interval = module.params["poll_interval"]
    task_id = module.params["task_id"]

    try:
        token = get_bearer_token(
            base_url,
            module.params["username"],
            module.params["password"],
            module.params["validate_certs"],
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

    start_time = time.time()
    last_status = None
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            module.fail_json(
                msg=f"Task {task_id} timed out after {timeout}s",
                task_id=task_id,
            )

        try:
            task = get_task_status(
                base_url, token, task_id, module.params["validate_certs"]
            )
        except HTTPError as e:
            body = ""
            try:
                body = e.read().decode()
            except Exception:
                pass
            module.fail_json(
                msg=f"Failed to poll task {task_id}: {e}",
                status_code=e.code,
                response_body=body,
            )
        except URLError as e:
            module.fail_json(msg=f"Failed to poll task {task_id}: {e}")

        status = task.get("status", "UNKNOWN")
        progress = task.get("progressPercent", 0)

        # Print progress every status change or every 2 minutes
        if status != last_status or elapsed % 120 < module.params["poll_interval"]:
            msg = f"Task {task_id}: {status} ({progress}%) — elapsed {int(elapsed)}s"
            module.debug(msg)
            last_status = status
        if status == "SUCCESSFUL":
            module.exit_json(
                changed=True,
                task_id=task_id,
                status=status,
                task=task,
            )
        elif status in ("FAILED", "CANCELLED"):
            errors = task.get("errors", [])
            module.fail_json(
                msg=f"Task {task_id} {status}",
                task_id=task_id,
                status=status,
                errors=errors,
                task=task,
            )

        time.sleep(poll_interval)


def main():
    run_module()


if __name__ == "__main__":
    main()

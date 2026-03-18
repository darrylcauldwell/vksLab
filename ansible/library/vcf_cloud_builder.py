#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Ansible module for VCF Cloud Builder bringup API."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vcf_cloud_builder
short_description: Drive VCF Cloud Builder bringup
description:
  - Validates or deploys a VCF management domain via the Cloud Builder REST API.
  - Uses Basic Auth against the Cloud Builder appliance.
options:
  hostname:
    description: Cloud Builder hostname or IP.
    required: true
    type: str
  username:
    description: Cloud Builder admin username.
    required: true
    type: str
  password:
    description: Cloud Builder admin password.
    required: true
    type: str
    no_log: true
  state:
    description: >
      C(validated) runs pre-flight validation only.
      C(deployed) starts bringup and polls until complete.
    required: true
    type: str
    choices: [validated, deployed]
  spec:
    description: >
      Bringup specification as a dict or path to a JSON file.
    required: true
    type: raw
  timeout:
    description: Maximum wait time in seconds for deployment.
    required: false
    type: int
    default: 7200
  poll_interval:
    description: Seconds between status checks during deployment.
    required: false
    type: int
    default: 60
  validate_certs:
    description: Whether to validate SSL certificates.
    required: false
    type: bool
    default: false
"""

import base64
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


def api_request(url, method, auth_header, data=None, validate_certs=False):
    """Make an authenticated API request to Cloud Builder."""
    payload = json.dumps(data).encode() if data else None
    req = Request(url, data=payload, method=method)
    req.add_header("Authorization", auth_header)
    req.add_header("Content-Type", "application/json")
    ctx = make_ssl_context(validate_certs)
    resp = urlopen(req, context=ctx)
    return json.loads(resp.read().decode())


def run_module():
    module_args = dict(
        hostname=dict(type="str", required=True),
        username=dict(type="str", required=True),
        password=dict(type="str", required=True, no_log=True),
        state=dict(type="str", required=True, choices=["validated", "deployed"]),
        spec=dict(type="raw", required=True),
        timeout=dict(type="int", required=False, default=7200),
        poll_interval=dict(type="int", required=False, default=60),
        validate_certs=dict(type="bool", required=False, default=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(changed=False, msg="Check mode — no action taken")

    base_url = f"https://{module.params['hostname']}"
    creds = f"{module.params['username']}:{module.params['password']}"
    auth_header = f"Basic {base64.b64encode(creds.encode()).decode()}"
    state = module.params["state"]
    validate_certs = module.params["validate_certs"]

    # Load spec — either a dict or a path to a JSON file
    spec = module.params["spec"]
    if isinstance(spec, str) and os.path.isfile(spec):
        try:
            with open(spec) as f:
                spec = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            module.fail_json(msg=f"Failed to load spec file: {e}")

    if not isinstance(spec, dict):
        module.fail_json(msg="spec must be a dict or path to a JSON file")

    try:
        if state == "validated":
            result = api_request(
                f"{base_url}/v1/sddcs/validations",
                "POST",
                auth_header,
                data=spec,
                validate_certs=validate_certs,
            )
            module.exit_json(
                changed=False,
                validation_id=result.get("id"),
                result=result,
            )

        elif state == "deployed":
            result = api_request(
                f"{base_url}/v1/sddcs",
                "POST",
                auth_header,
                data=spec,
                validate_certs=validate_certs,
            )
            deployment_id = result.get("id")

            # Poll until deployment completes
            timeout = module.params["timeout"]
            poll_interval = module.params["poll_interval"]
            start_time = time.time()

            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    module.fail_json(
                        msg=f"Bringup timed out after {timeout}s",
                        deployment_id=deployment_id,
                    )

                status_resp = api_request(
                    f"{base_url}/v1/sddcs/{deployment_id}",
                    "GET",
                    auth_header,
                    validate_certs=validate_certs,
                )
                status = status_resp.get("status", "UNKNOWN")

                if status == "COMPLETED":
                    module.exit_json(
                        changed=True,
                        deployment_id=deployment_id,
                        status=status,
                        result=status_resp,
                    )
                elif status in ("FAILED", "CANCELLED"):
                    module.fail_json(
                        msg=f"Bringup {status}",
                        deployment_id=deployment_id,
                        status=status,
                        result=status_resp,
                    )

                time.sleep(poll_interval)

    except (URLError, HTTPError) as e:
        module.fail_json(msg=f"Cloud Builder API error: {e}")


def main():
    run_module()


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Ansible module for VCF management domain bringup via the VCF Installer API."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vcf_cloud_builder
short_description: Drive VCF management domain bringup
description:
  - Validates or deploys a VCF management domain via the VCF Installer REST API.
  - Authenticates via token (POST /v1/tokens) then uses Bearer auth.
  - Validation is asynchronous — polls until completion.
  - Bringup is asynchronous — polls until completion (up to timeout).
options:
  hostname:
    description: VCF Installer hostname or IP.
    required: true
    type: str
  username:
    description: VCF Installer admin username (e.g. admin@local).
    required: true
    type: str
  password:
    description: VCF Installer admin password.
    required: true
    type: str
    no_log: true
  state:
    description: >
      C(validated) runs pre-flight validation only (async, polls until done).
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
    description: Maximum wait time in seconds for validation or deployment.
    required: false
    type: int
    default: 7200
  poll_interval:
    description: Seconds between status checks.
    required: false
    type: int
    default: 60
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


def get_auth_token(base_url, username, password, validate_certs):
    """Obtain a bearer token from POST /v1/tokens."""
    token_data = {"username": username, "password": password}
    token_payload = json.dumps(token_data).encode()
    req = Request(f"{base_url}/v1/tokens", data=token_payload, method="POST")
    req.add_header("Content-Type", "application/json")
    ctx = make_ssl_context(validate_certs)
    resp = urlopen(req, context=ctx)
    result = json.loads(resp.read().decode())
    access_token = result.get("accessToken")
    if not access_token:
        raise RuntimeError(f"Token response missing accessToken: {result}")
    return f"Bearer {access_token}"


def api_request(url, method, auth_header, data=None, validate_certs=False):
    """Make an authenticated API request."""
    payload = json.dumps(data).encode() if data else None
    req = Request(url, data=payload, method=method)
    req.add_header("Authorization", auth_header)
    req.add_header("Content-Type", "application/json")
    ctx = make_ssl_context(validate_certs)
    resp = urlopen(req, context=ctx)
    body = resp.read().decode()
    return json.loads(body) if body else {}


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
    username = module.params["username"]
    password = module.params["password"]
    state = module.params["state"]
    validate_certs = module.params["validate_certs"]
    timeout = module.params["timeout"]
    poll_interval = module.params["poll_interval"]

    # Obtain initial bearer token
    try:
        auth_header = get_auth_token(base_url, username, password, validate_certs)
    except (URLError, HTTPError, RuntimeError) as e:
        module.fail_json(msg=f"Failed to obtain API token: {e}")

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

    def api_get_with_token_refresh(url):
        """GET request with automatic token refresh on 401."""
        nonlocal auth_header
        try:
            return api_request(url, "GET", auth_header,
                               validate_certs=validate_certs)
        except HTTPError as e:
            if e.code == 401:
                # Token expired — re-authenticate and retry
                auth_header = get_auth_token(base_url, username, password,
                                             validate_certs)
                return api_request(url, "GET", auth_header,
                                   validate_certs=validate_certs)
            raise

    try:
        if state == "validated":
            # POST starts async validation — returns an ID
            result = api_request(
                f"{base_url}/v1/sddcs/validations",
                "POST",
                auth_header,
                data=spec,
                validate_certs=validate_certs,
            )
            validation_id = result.get("id")
            if not validation_id:
                module.fail_json(
                    msg=f"Validation POST did not return an ID: {result}")

            # Poll until validation completes
            start_time = time.time()
            while True:
                if time.time() - start_time > timeout:
                    module.fail_json(
                        msg=f"Validation timed out after {timeout}s",
                        validation_id=validation_id,
                    )

                status_resp = api_get_with_token_refresh(
                    f"{base_url}/v1/sddcs/validations/{validation_id}")

                exec_status = status_resp.get("executionStatus", "UNKNOWN")

                if exec_status == "COMPLETED":
                    result_status = status_resp.get("resultStatus", "UNKNOWN")
                    if result_status == "SUCCEEDED":
                        module.exit_json(
                            changed=False,
                            validation_id=validation_id,
                            result_status=result_status,
                            result=status_resp,
                        )
                    else:
                        # FAILED or FAILED_WITH_WARNINGS
                        checks = status_resp.get("validationChecks", [])
                        failed_checks = [
                            c for c in checks
                            if c.get("resultStatus") in ("FAILED",)
                        ]
                        module.fail_json(
                            msg=f"Validation {result_status}",
                            validation_id=validation_id,
                            result_status=result_status,
                            failed_checks=failed_checks,
                            result=status_resp,
                        )

                elif exec_status in ("FAILED", "CANCELLED"):
                    module.fail_json(
                        msg=f"Validation execution {exec_status}",
                        validation_id=validation_id,
                        result=status_resp,
                    )

                # IN_PROGRESS or other — keep polling
                time.sleep(poll_interval)

        elif state == "deployed":
            result = api_request(
                f"{base_url}/v1/sddcs",
                "POST",
                auth_header,
                data=spec,
                validate_certs=validate_certs,
            )
            deployment_id = result.get("id")
            if not deployment_id:
                module.fail_json(
                    msg=f"Bringup POST did not return an ID: {result}")

            # Poll until deployment completes
            start_time = time.time()
            while True:
                if time.time() - start_time > timeout:
                    module.fail_json(
                        msg=f"Bringup timed out after {timeout}s",
                        deployment_id=deployment_id,
                    )

                status_resp = api_get_with_token_refresh(
                    f"{base_url}/v1/sddcs/{deployment_id}")

                status = status_resp.get("status", "UNKNOWN")

                if status == "COMPLETED_WITH_SUCCESS":
                    module.exit_json(
                        changed=True,
                        deployment_id=deployment_id,
                        status=status,
                        result=status_resp,
                    )
                elif status in ("COMPLETED_WITH_FAILURE", "ROLLBACK_SUCCESS"):
                    sub_tasks = status_resp.get("sddcSubTasks", [])
                    failed_tasks = [
                        t for t in sub_tasks
                        if t.get("status") != "COMPLETED_WITH_SUCCESS"
                    ]
                    module.fail_json(
                        msg=f"Bringup {status}",
                        deployment_id=deployment_id,
                        status=status,
                        failed_tasks=failed_tasks,
                        result=status_resp,
                    )

                # IN_PROGRESS — keep polling
                time.sleep(poll_interval)

    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass
        module.fail_json(
            msg=f"Cloud Builder API error: {e}",
            status_code=e.code,
            response_body=body,
        )
    except URLError as e:
        module.fail_json(msg=f"Cloud Builder API error: {e}")


def main():
    run_module()


if __name__ == "__main__":
    main()

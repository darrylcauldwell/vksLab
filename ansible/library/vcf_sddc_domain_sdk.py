#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Ansible module for SDDC Manager domain creation using VCF SDK."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vcf_sddc_domain_sdk
short_description: Validate and create SDDC Manager domains using VCF SDK
description:
  - Validates domain specification against SDDC Manager
  - Creates workload domains
  - Polls task completion
  - Wraps VCF SDK for better error handling
options:
  sddc_hostname:
    description: SDDC Manager hostname or IP
    required: true
    type: str
  username:
    description: SDDC Manager username
    required: true
    type: str
  password:
    description: SDDC Manager password
    required: true
    type: str
    no_log: true
  state:
    description: >
      C(validated) validates the domain spec without creating.
      C(present) validates and creates the domain.
    required: true
    type: str
    choices: [validated, present]
  domain_spec:
    description: Domain creation specification (JSON)
    required: true
    type: dict
  timeout:
    description: Maximum wait time in seconds for task completion
    required: false
    type: int
    default: 5400
  poll_interval:
    description: Task polling interval in seconds
    required: false
    type: int
    default: 60
"""

EXAMPLES = r"""
- name: Validate workload domain spec
  vcf_sddc_domain_sdk:
    sddc_hostname: sddc-manager.lab.dreamfold.dev
    username: admin@local
    password: "{{ sddc_admin_password }}"
    state: validated
    domain_spec: "{{ vcf_wld_domain_spec }}"

- name: Create workload domain
  vcf_sddc_domain_sdk:
    sddc_hostname: sddc-manager.lab.dreamfold.dev
    username: admin@local
    password: "{{ sddc_admin_password }}"
    state: present
    domain_spec: "{{ vcf_wld_domain_spec }}"
    timeout: 5400
"""

import json
import sys
from ansible.module_utils.basic import AnsibleModule

try:
    from vcf_sdk import SDDCManager
    from vcf_sdk.exceptions import ValidationError, TaskFailedError, TimeoutError as SDKTimeoutError
    HAS_SDK = True
except ImportError:
    HAS_SDK = False


def parse_nested_errors(response_body):
    """Extract nested validation errors from SDDC Manager response."""
    try:
        data = json.loads(response_body)
        errors = []

        if "nestedErrors" in data:
            for error in data["nestedErrors"]:
                msg = error.get("message", "Unknown error")
                if error.get("remediationMessage"):
                    msg += f" ({error['remediationMessage']})"
                errors.append(msg)

        return " | ".join(errors) if errors else data.get("message", "Unknown error")
    except:
        return response_body


def main():
    """Main module function."""
    module = AnsibleModule(
        argument_spec=dict(
            sddc_hostname=dict(type="str", required=True),
            username=dict(type="str", required=True),
            password=dict(type="str", required=True, no_log=True),
            state=dict(type="str", required=True, choices=["validated", "present"]),
            domain_spec=dict(type="dict", required=True),
            timeout=dict(type="int", default=5400),
            poll_interval=dict(type="int", default=60),
        ),
        supports_check_mode=False,
    )

    if not HAS_SDK:
        module.fail_json(
            msg="VCF SDK not found. Install: pip install -e /path/to/vcf-sdk"
        )

    params = module.params
    sddc_hostname = params["sddc_hostname"]
    username = params["username"]
    password = params["password"]
    state = params["state"]
    domain_spec = params["domain_spec"]
    timeout = params["timeout"]
    poll_interval = params["poll_interval"]

    try:
        with SDDCManager(
            hostname=sddc_hostname,
            username=username,
            password=password,
            verify_ssl=False,
        ) as sddc:

            # Validate spec
            try:
                validation = sddc.domains.validate(domain_spec)
                module.debug(f"Validation passed: {validation.id}")
            except ValidationError as e:
                error_msg = parse_nested_errors(e.response_body) if e.response_body else str(e)
                module.fail_json(
                    msg=f"Domain spec validation failed: {error_msg}",
                    response_body=e.response_body,
                    status_code=e.status_code,
                )

            # If only validating, return success
            if state == "validated":
                module.exit_json(
                    changed=False,
                    msg="Domain spec validation passed",
                    validation_id=validation.id,
                )

            # Create domain
            try:
                create_task = sddc.domains.create(domain_spec, validate=False)
                module.debug(f"Domain creation task started: {create_task.id}")

                # Wait for completion
                final_task = sddc.tasks.wait_for_completion(
                    create_task.id,
                    timeout=timeout,
                    poll_interval=poll_interval,
                )

                module.exit_json(
                    changed=True,
                    msg="Domain created successfully",
                    task_id=create_task.id,
                    task_status=final_task.status,
                )

            except TaskFailedError as e:
                module.fail_json(
                    msg=f"Domain creation task failed: {e.message}",
                    task_id=e.task_id,
                    task_status=e.status,
                    task_errors=e.errors,
                )
            except SDKTimeoutError as e:
                module.fail_json(
                    msg=f"Domain creation timed out after {timeout}s: {str(e)}",
                )

    except Exception as e:
        module.fail_json(
            msg=f"Unexpected error: {str(e)}",
            exception=str(e),
        )


if __name__ == "__main__":
    main()

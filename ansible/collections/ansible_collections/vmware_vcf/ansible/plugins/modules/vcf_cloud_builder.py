#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Ansible module for VCF Cloud Builder — SDDC bringup and validation."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vcf_cloud_builder
short_description: Drive VCF SDDC bringup via Cloud Builder API
description:
  - Validate and deploy management domain via VCF Cloud Builder.
  - Supports known-safe warning bypass for nested lab environments.
version_added: "0.1.0"
options:
  state:
    description: Action to perform.
    type: str
    choices: [validated, deployed]
    default: validated
  hostname:
    description: Cloud Builder FQDN or IP.
    type: str
    required: true
  username:
    description: Cloud Builder username.
    type: str
    required: true
  password:
    description: Cloud Builder password.
    type: str
    required: true
    no_log: true
  spec:
    description: SDDC bringup spec (JSON dict).
    type: dict
    required: true
  validate_certs:
    description: Verify SSL certificates.
    type: bool
    default: false
  nested_lab:
    description: >
      If true, bypass known-safe validation failures for nested labs
      (VSAN_ESA_HOST_NOT_HCL_COMPATIBLE, NO_VSAN_ESA_CERTIFIED_DISKS, EXISTING_SDDC_VALIDATION_WARNING).
    type: bool
    default: false
  validation_timeout:
    description: Timeout for validation in seconds.
    type: int
    default: 600
  deploy_timeout:
    description: Timeout for deployment in seconds.
    type: int
    default: 14400
  poll_interval:
    description: Poll interval in seconds.
    type: int
    default: 60
"""

EXAMPLES = r"""
- name: Validate bringup spec
  vmware_vcf.ansible.vcf_cloud_builder:
    hostname: vcf-builder.lab.dev
    username: admin
    password: "{{ vault_cb_password }}"
    state: validated
    nested_lab: true
    spec: "{{ bringup_spec }}"

- name: Deploy management domain
  vmware_vcf.ansible.vcf_cloud_builder:
    hostname: vcf-builder.lab.dev
    username: admin
    password: "{{ vault_cb_password }}"
    state: deployed
    nested_lab: true
    spec: "{{ bringup_spec }}"
    deploy_timeout: 14400
"""

RETURN = r"""
validation_id:
  description: Validation task ID.
  returned: always
  type: str
result_status:
  description: Validation result status.
  returned: on validated
  type: str
deployment_id:
  description: Deployment task ID.
  returned: on deployed
  type: str
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from vcf_sdk import CloudBuilder
    from vcf_sdk.exceptions import ValidationError, TimeoutError

    HAS_VCF_SDK = True
except ImportError:
    HAS_VCF_SDK = False

KNOWN_SAFE_CODES = {
    "VSAN_ESA_HOST_NOT_HCL_COMPATIBLE",
    "NO_VSAN_ESA_CERTIFIED_DISKS",
    "EXISTING_SDDC_VALIDATION_WARNING",
}


def _is_all_known_safe(failed_checks):
    """Check if all failed validation checks are known-safe for nested labs."""
    for check in failed_checks:
        error_code = check.get("errorResponse", {}).get("errorCode", "")
        if error_code in KNOWN_SAFE_CODES:
            continue
        nested_errors = check.get("nestedErrors", [])
        if all(e.get("errorCode") in KNOWN_SAFE_CODES for e in nested_errors):
            continue
        return False
    return True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type="str", choices=["validated", "deployed", "depot"], default="validated"),
            hostname=dict(type="str", required=True),
            username=dict(type="str", required=True),
            password=dict(type="str", required=True, no_log=True),
            spec=dict(type="dict"),
            depot_spec=dict(type="dict"),
            validate_certs=dict(type="bool", default=False),
            nested_lab=dict(type="bool", default=False),
            validation_timeout=dict(type="int", default=600),
            deploy_timeout=dict(type="int", default=14400),
            poll_interval=dict(type="int", default=60),
        ),
        supports_check_mode=True,
    )

    if not HAS_VCF_SDK:
        module.fail_json(msg="vmware-vcf Python package required. pip install vmware-vcf")

    state = module.params["state"]
    nested_lab = module.params["nested_lab"]
    result = dict(changed=False)

    cb = CloudBuilder(
        hostname=module.params["hostname"],
        username=module.params["username"],
        password=module.params["password"],
        verify_ssl=module.params["validate_certs"],
    )

    try:
        # Depot configuration
        if state == "depot":
            if module.check_mode:
                module.exit_json(changed=True, msg="Would configure depot")
            depot_resp = cb.set_depot(module.params["depot_spec"])
            result["changed"] = True
            result["depot"] = depot_resp
            module.exit_json(**result)

        # Validate
        if module.check_mode:
            module.exit_json(changed=True, msg=f"Would {state} SDDC")

        val_resp = cb.start_validation(module.params["spec"])
        validation_id = val_resp.get("id")
        result["validation_id"] = validation_id

        try:
            val_result = cb.wait_for_validation(
                validation_id,
                timeout=module.params["validation_timeout"],
                poll_interval=module.params["poll_interval"],
            )
            result["result_status"] = "SUCCEEDED"
        except ValidationError:
            # Check if failures are known-safe
            val_status = cb.get_validation(validation_id)
            checks = val_status.get("validationChecks", [])
            failed = [c for c in checks if c.get("resultStatus") == "FAILED"]

            if nested_lab and failed and _is_all_known_safe(failed):
                result["result_status"] = "WARNING"
                result["warnings"] = failed
            else:
                module.fail_json(
                    msg="Validation failed",
                    validation_id=validation_id,
                    failed_checks=failed,
                )

        if state == "validated":
            module.exit_json(**result)

        # Deploy
        deploy_resp = cb.start_bringup(module.params["spec"])
        deployment_id = deploy_resp.get("id")
        result["deployment_id"] = deployment_id
        result["changed"] = True

        import time

        start = time.time()
        timeout = module.params["deploy_timeout"]
        poll = module.params["poll_interval"]

        while True:
            status = cb.get_sddc(deployment_id)
            exec_status = status.get("status", "")

            if exec_status in ("COMPLETED_WITH_SUCCESS", "COMPLETED_WITH_FAILURE"):
                result["deployment_status"] = exec_status
                if "FAILURE" in exec_status:
                    module.fail_json(msg=f"Deployment {exec_status}", **result)
                break

            if time.time() - start > timeout:
                module.fail_json(msg=f"Deployment timed out after {timeout}s", **result)

            time.sleep(poll)

    except Exception as e:
        module.fail_json(msg=str(e))
    finally:
        cb.close()

    module.exit_json(**result)


if __name__ == "__main__":
    main()

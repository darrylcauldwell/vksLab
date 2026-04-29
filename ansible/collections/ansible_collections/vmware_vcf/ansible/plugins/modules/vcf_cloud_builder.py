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
  - Uses discrete states so Ansible can poll with until/retries for visible progress.
version_added: "0.1.0"
options:
  state:
    description: Action to perform.
    type: str
    choices: [depot, start_validation, get_validation, start_bringup, get_bringup]
    required: true
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
  depot_spec:
    description: Depot configuration spec (JSON dict).
    type: dict
  id:
    description: Validation or bringup task ID (for get_validation/get_bringup).
    type: str
  validate_certs:
    description: Verify SSL certificates.
    type: bool
    default: false
"""

EXAMPLES = r"""
- name: Configure depot
  vmware_vcf.ansible.vcf_cloud_builder:
    hostname: vcf-installer.lab.dev
    username: admin@local
    password: "{{ password }}"
    state: depot
    depot_spec: "{{ depot_spec }}"

- name: Start validation
  vmware_vcf.ansible.vcf_cloud_builder:
    hostname: vcf-installer.lab.dev
    username: admin@local
    password: "{{ password }}"
    state: start_validation
    spec: "{{ bringup_spec }}"
  register: validation

- name: Poll validation
  vmware_vcf.ansible.vcf_cloud_builder:
    hostname: vcf-installer.lab.dev
    username: admin@local
    password: "{{ password }}"
    state: get_validation
    id: "{{ validation.id }}"
  register: val_status
  until: val_status.execution_status == 'COMPLETED'
  retries: 360
  delay: 10

- name: Start bringup
  vmware_vcf.ansible.vcf_cloud_builder:
    hostname: vcf-installer.lab.dev
    username: admin@local
    password: "{{ password }}"
    state: start_bringup
    spec: "{{ bringup_spec }}"
  register: bringup

- name: Poll bringup
  vmware_vcf.ansible.vcf_cloud_builder:
    hostname: vcf-installer.lab.dev
    username: admin@local
    password: "{{ password }}"
    state: get_bringup
    id: "{{ bringup.id }}"
  register: bringup_status
  until: bringup_status.status in ['COMPLETED_WITH_SUCCESS', 'COMPLETED_WITH_FAILURE']
  retries: 240
  delay: 60
"""

RETURN = r"""
id:
  description: Validation or bringup task ID.
  returned: on start_validation, start_bringup
  type: str
execution_status:
  description: Validation execution status (IN_PROGRESS, COMPLETED).
  returned: on get_validation
  type: str
result_status:
  description: Validation result (SUCCEEDED, FAILED).
  returned: on get_validation when completed
  type: str
validation_checks:
  description: List of validation check results.
  returned: on get_validation when completed
  type: list
status:
  description: Bringup status.
  returned: on get_bringup
  type: str
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from vcf_sdk import CloudBuilder
    HAS_VCF_SDK = True
except ImportError:
    HAS_VCF_SDK = False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(
                type="str",
                choices=["depot", "start_validation", "get_validation", "start_bringup", "get_bringup"],
                required=True,
            ),
            hostname=dict(type="str", required=True),
            username=dict(type="str", default=""),
            password=dict(type="str", default="", no_log=True),
            bearer_token=dict(type="str", no_log=True),
            spec=dict(type="dict"),
            depot_spec=dict(type="dict"),
            id=dict(type="str"),
            validate_certs=dict(type="bool", default=False),
        ),
        supports_check_mode=True,
    )

    if not HAS_VCF_SDK:
        module.fail_json(msg="vmware-vcf Python package required. pip install vmware-vcf")

    state = module.params["state"]
    result = dict(changed=False)

    try:
        cb = CloudBuilder(
            hostname=module.params["hostname"],
            username=module.params["username"],
            password=module.params["password"],
            verify_ssl=module.params["validate_certs"],
            bearer_token=module.params.get("bearer_token"),
        )

        if state == "depot":
            if module.check_mode:
                module.exit_json(changed=True, msg="Would configure depot")
            depot_resp = cb.set_depot(module.params["depot_spec"])
            result["changed"] = True
            result["depot"] = depot_resp

        elif state == "start_validation":
            if module.check_mode:
                module.exit_json(changed=True, msg="Would start validation")
            resp = cb.start_validation(module.params["spec"])
            result["changed"] = True
            result["id"] = resp.get("id")

        elif state == "get_validation":
            resp = cb.get_validation(module.params["id"])
            result["execution_status"] = resp.get("executionStatus", "UNKNOWN")
            result["result_status"] = resp.get("resultStatus", "")
            result["validation_checks"] = resp.get("validationChecks", [])
            checks = resp.get("validationChecks", [])
            passed = len([c for c in checks if c.get("resultStatus") == "SUCCEEDED"])
            failed = len([c for c in checks if c.get("resultStatus") == "FAILED"])
            total = len(checks)
            result["msg"] = f"Validation {result['execution_status']}: {passed}/{total} passed, {failed} failed"

        elif state == "start_bringup":
            if module.check_mode:
                module.exit_json(changed=True, msg="Would start bringup")
            resp = cb.start_bringup(module.params["spec"])
            result["changed"] = True
            result["id"] = resp.get("id")

        elif state == "get_bringup":
            resp = cb.get_sddc(module.params["id"])
            result["status"] = resp.get("status", "UNKNOWN")
            result["msg"] = f"Bringup status: {result['status']}"

        # Return token if we authenticated (not using pre-existing bearer_token)
        if not module.params.get("bearer_token") and cb.access_token:
            result["bearer_token"] = cb.access_token
            result["refresh_token"] = cb.refresh_token

        cb.close()

    except Exception as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)


if __name__ == "__main__":
    main()

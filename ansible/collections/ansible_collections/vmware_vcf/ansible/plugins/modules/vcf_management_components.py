#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Ansible module for VCF Management Components deployment."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vcf_management_components
short_description: Deploy VCF Management Components via SDDC Manager
description:
  - Deploy VCF Operations, Collector, and Fleet Management.
  - Check deployment status.
version_added: "0.5.0"
options:
  state:
    description: Desired state.
    type: str
    choices: [present, info]
    default: present
  spec:
    description: VCF Management Components deployment spec.
    type: dict
  validate:
    description: Validate spec before deploying.
    type: bool
    default: true
  wait:
    description: Wait for deployment to complete.
    type: bool
    default: true
  wait_timeout:
    description: Timeout in seconds for deployment.
    type: int
    default: 7200
extends_documentation_fragment:
  - vmware_vcf.ansible.sddc_auth
"""

EXAMPLES = r"""
- name: Check management components status
  vmware_vcf.ansible.vcf_management_components:
    sddc_hostname: sddc-manager.lab.dev
    sddc_username: admin@local
    sddc_password: "{{ vault_sddc_password }}"
    state: info

- name: Deploy management components
  vmware_vcf.ansible.vcf_management_components:
    sddc_hostname: sddc-manager.lab.dev
    sddc_username: admin@local
    sddc_password: "{{ vault_sddc_password }}"
    state: present
    spec: "{{ vcf_mgmt_components_spec }}"
"""

RETURN = r"""
result:
  description: Deployment status or task details.
  returned: always
  type: raw
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.vmware_vcf.ansible.plugins.module_utils.vcf_common import (
        sddc_argument_spec,
        get_sddc_client,
    )
except ImportError:
    pass


def main():
    argument_spec = sddc_argument_spec()
    argument_spec.update(
        state=dict(type="str", choices=["present", "info"], default="present"),
        spec=dict(type="dict"),
        validate=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=7200),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    sddc = get_sddc_client(module)
    state = module.params["state"]
    result = dict(changed=False)

    try:
        if state == "info":
            status = sddc.management_components.get()
            result["result"] = status

        elif state == "present":
            spec = module.params.get("spec")
            if not spec:
                module.fail_json(msg="spec is required for state=present")
            if module.check_mode:
                module.exit_json(changed=True, msg="Would deploy management components")
            task = sddc.management_components.deploy(
                spec, validate=module.params["validate"]
            )
            result["changed"] = True
            result["task"] = {"id": task.id, "status": task.status.value}
            if module.params["wait"]:
                final = sddc.tasks.wait_for_completion(
                    task.id, timeout=module.params["wait_timeout"]
                )
                result["task"]["status"] = final.status.value
            result["result"] = result["task"]

    except Exception as e:
        module.fail_json(msg=str(e))
    finally:
        sddc.close()

    module.exit_json(**result)


if __name__ == "__main__":
    main()

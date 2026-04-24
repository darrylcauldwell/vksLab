#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Ansible module for vCenter Supervisor Services (VKS Standard Packages)."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vcf_vcenter_supervisor_service
short_description: Manage vCenter Supervisor Services
description:
  - List, install, and enable Supervisor Services (VKS Standard Packages).
  - Used for cert-manager, Contour, Harbor, and Velero.
version_added: "0.5.0"
options:
  action:
    description: Action to perform.
    type: str
    choices:
      - list_services
      - list_versions
      - list_cluster_services
      - get_cluster_service
      - enable_service
    required: true
  cluster_id:
    description: Supervisor cluster identifier.
    type: str
  service_id:
    description: Supervisor service identifier (e.g., cert-manager, contour, harbor, velero).
    type: str
  spec:
    description: Service configuration spec (for enable_service).
    type: dict
extends_documentation_fragment:
  - vmware_vcf.ansible.vcenter_auth
"""

EXAMPLES = r"""
- name: List available Supervisor Services
  vmware_vcf.ansible.vcf_vcenter_supervisor_service:
    vcenter_hostname: vcenter.lab.dev
    vcenter_username: administrator@vsphere.local
    vcenter_password: "{{ vault_vcenter_password }}"
    action: list_services

- name: List versions of cert-manager
  vmware_vcf.ansible.vcf_vcenter_supervisor_service:
    vcenter_hostname: vcenter.lab.dev
    vcenter_username: administrator@vsphere.local
    vcenter_password: "{{ vault_vcenter_password }}"
    action: list_versions
    service_id: cert-manager

- name: Enable cert-manager on cluster
  vmware_vcf.ansible.vcf_vcenter_supervisor_service:
    vcenter_hostname: vcenter.lab.dev
    vcenter_username: administrator@vsphere.local
    vcenter_password: "{{ vault_vcenter_password }}"
    action: enable_service
    cluster_id: "{{ supervisor_cluster_id }}"
    service_id: cert-manager
    spec:
      version: "1.14.5"
"""

RETURN = r"""
result:
  description: Operation result.
  returned: always
  type: raw
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.vmware_vcf.ansible.plugins.module_utils.vcf_common import (
        vcenter_argument_spec,
        get_vcenter_client,
    )
except ImportError:
    pass


def main():
    argument_spec = vcenter_argument_spec()
    argument_spec.update(
        action=dict(
            type="str",
            required=True,
            choices=[
                "list_services",
                "list_versions",
                "list_cluster_services",
                "get_cluster_service",
                "enable_service",
            ],
        ),
        cluster_id=dict(type="str"),
        service_id=dict(type="str"),
        spec=dict(type="dict"),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    vc = get_vcenter_client(module)
    action = module.params["action"]
    result = dict(changed=False)

    try:
        if action == "list_services":
            services = vc.namespaces.list_supervisor_services()
            result["result"] = services

        elif action == "list_versions":
            service_id = module.params.get("service_id")
            if not service_id:
                module.fail_json(msg="service_id required for list_versions")
            versions = vc.namespaces.list_supervisor_service_versions(service_id)
            result["result"] = versions

        elif action == "list_cluster_services":
            cluster_id = module.params.get("cluster_id")
            if not cluster_id:
                module.fail_json(msg="cluster_id required for list_cluster_services")
            services = vc.namespaces.list_cluster_supervisor_services(cluster_id)
            result["result"] = services

        elif action == "get_cluster_service":
            cluster_id = module.params.get("cluster_id")
            service_id = module.params.get("service_id")
            if not cluster_id or not service_id:
                module.fail_json(
                    msg="cluster_id and service_id required for get_cluster_service"
                )
            service = vc.namespaces.get_cluster_supervisor_service(
                cluster_id, service_id
            )
            result["result"] = service

        elif action == "enable_service":
            cluster_id = module.params.get("cluster_id")
            service_id = module.params.get("service_id")
            spec = module.params.get("spec")
            if not cluster_id or not service_id:
                module.fail_json(
                    msg="cluster_id and service_id required for enable_service"
                )
            if module.check_mode:
                module.exit_json(
                    changed=True,
                    msg=f"Would enable {service_id} on cluster {cluster_id}",
                )
            vc.namespaces.enable_supervisor_service_on_cluster(
                cluster_id, service_id, spec or {}
            )
            result["changed"] = True
            result["result"] = f"Service {service_id} enabled on cluster {cluster_id}"

    except Exception as e:
        module.fail_json(msg=str(e))
    finally:
        vc.close()

    module.exit_json(**result)


if __name__ == "__main__":
    main()

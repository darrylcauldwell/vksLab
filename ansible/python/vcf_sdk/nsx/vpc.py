"""VPC multi-tenancy management for NSX-T Policy API (NSX 4.2+).

All VPC paths are under /orgs/{org-id}/projects/{project-id}/...
The NSXManager prepends /policy/api/v1 to all requests.
"""

from typing import Any, Dict, List

from vcf_sdk.models.nsx import Project, VPC, VPCSubnet, VPCSubnetPort
from vcf_sdk.models.nsx.security import SecurityPolicy, GatewayPolicy, Group
from vcf_sdk.models.nsx.nat import NATRule
from vcf_sdk.models.nsx.gateway import StaticRoute
from vcf_sdk.nsx.base import NSXBaseManager

DEFAULT_ORG = "default"


class ProjectManager(NSXBaseManager):
    """Manage NSX multi-tenancy projects."""

    def list(self, org: str = DEFAULT_ORG) -> List[Project]:
        return self._list(f"/orgs/{org}/projects", Project)

    def get(self, project_id: str, org: str = DEFAULT_ORG) -> Project:
        return self._get(f"/orgs/{org}/projects/{project_id}", Project)

    def create_or_update(
        self, project_id: str, spec: Dict[str, Any], org: str = DEFAULT_ORG
    ) -> Dict[str, Any]:
        spec.setdefault("id", project_id)
        return self._create_or_update(f"/orgs/{org}/projects/{project_id}", spec)

    def delete(self, project_id: str, org: str = DEFAULT_ORG) -> None:
        self._delete(f"/orgs/{org}/projects/{project_id}")


class VPCManager(NSXBaseManager):
    """Manage NSX VPCs and all VPC sub-resources."""

    def _vpc_base(self, org: str, project: str) -> str:
        return f"/orgs/{org}/projects/{project}/vpcs"

    def _vpc_path(self, org: str, project: str, vpc_id: str) -> str:
        return f"{self._vpc_base(org, project)}/{vpc_id}"

    # VPC CRUD

    def list(self, project: str, org: str = DEFAULT_ORG) -> List[VPC]:
        return self._list(self._vpc_base(org, project), VPC)

    def get(self, project: str, vpc_id: str, org: str = DEFAULT_ORG) -> VPC:
        return self._get(self._vpc_path(org, project, vpc_id), VPC)

    def create_or_update(
        self, project: str, vpc_id: str, spec: Dict[str, Any], org: str = DEFAULT_ORG
    ) -> Dict[str, Any]:
        spec.setdefault("id", vpc_id)
        return self._create_or_update(self._vpc_path(org, project, vpc_id), spec)

    def delete(self, project: str, vpc_id: str, org: str = DEFAULT_ORG) -> None:
        self._delete(self._vpc_path(org, project, vpc_id))

    # VPC Subnets

    def list_subnets(
        self, project: str, vpc_id: str, org: str = DEFAULT_ORG
    ) -> List[VPCSubnet]:
        return self._list(f"{self._vpc_path(org, project, vpc_id)}/subnets", VPCSubnet)

    def get_subnet(
        self, project: str, vpc_id: str, subnet_id: str, org: str = DEFAULT_ORG
    ) -> VPCSubnet:
        return self._get(
            f"{self._vpc_path(org, project, vpc_id)}/subnets/{subnet_id}", VPCSubnet
        )

    def create_or_update_subnet(
        self, project: str, vpc_id: str, subnet_id: str,
        spec: Dict[str, Any], org: str = DEFAULT_ORG
    ) -> Dict[str, Any]:
        spec.setdefault("id", subnet_id)
        return self._create_or_update(
            f"{self._vpc_path(org, project, vpc_id)}/subnets/{subnet_id}", spec
        )

    def delete_subnet(
        self, project: str, vpc_id: str, subnet_id: str, org: str = DEFAULT_ORG
    ) -> None:
        self._delete(f"{self._vpc_path(org, project, vpc_id)}/subnets/{subnet_id}")

    # VPC Subnet Ports

    def list_subnet_ports(
        self, project: str, vpc_id: str, subnet_id: str, org: str = DEFAULT_ORG
    ) -> List[VPCSubnetPort]:
        return self._list(
            f"{self._vpc_path(org, project, vpc_id)}/subnets/{subnet_id}/ports",
            VPCSubnetPort,
        )

    def create_or_update_subnet_port(
        self, project: str, vpc_id: str, subnet_id: str, port_id: str,
        spec: Dict[str, Any], org: str = DEFAULT_ORG
    ) -> Dict[str, Any]:
        spec.setdefault("id", port_id)
        return self._create_or_update(
            f"{self._vpc_path(org, project, vpc_id)}/subnets/{subnet_id}/ports/{port_id}", spec
        )

    # VPC Groups

    def list_groups(
        self, project: str, vpc_id: str, org: str = DEFAULT_ORG
    ) -> List[Group]:
        return self._list(f"{self._vpc_path(org, project, vpc_id)}/groups", Group)

    def create_or_update_group(
        self, project: str, vpc_id: str, group_id: str,
        spec: Dict[str, Any], org: str = DEFAULT_ORG
    ) -> Dict[str, Any]:
        spec.setdefault("id", group_id)
        return self._create_or_update(
            f"{self._vpc_path(org, project, vpc_id)}/groups/{group_id}", spec
        )

    def delete_group(
        self, project: str, vpc_id: str, group_id: str, org: str = DEFAULT_ORG
    ) -> None:
        self._delete(f"{self._vpc_path(org, project, vpc_id)}/groups/{group_id}")

    # VPC Security Policies + Rules

    def list_security_policies(
        self, project: str, vpc_id: str, org: str = DEFAULT_ORG
    ) -> List[SecurityPolicy]:
        return self._list(
            f"{self._vpc_path(org, project, vpc_id)}/security-policies", SecurityPolicy
        )

    def create_or_update_security_policy(
        self, project: str, vpc_id: str, policy_id: str,
        spec: Dict[str, Any], org: str = DEFAULT_ORG
    ) -> Dict[str, Any]:
        spec.setdefault("id", policy_id)
        return self._create_or_update(
            f"{self._vpc_path(org, project, vpc_id)}/security-policies/{policy_id}", spec
        )

    def delete_security_policy(
        self, project: str, vpc_id: str, policy_id: str, org: str = DEFAULT_ORG
    ) -> None:
        self._delete(
            f"{self._vpc_path(org, project, vpc_id)}/security-policies/{policy_id}"
        )

    # VPC Gateway Policies

    def list_gateway_policies(
        self, project: str, vpc_id: str, org: str = DEFAULT_ORG
    ) -> List[GatewayPolicy]:
        return self._list(
            f"{self._vpc_path(org, project, vpc_id)}/gateway-policies", GatewayPolicy
        )

    def create_or_update_gateway_policy(
        self, project: str, vpc_id: str, policy_id: str,
        spec: Dict[str, Any], org: str = DEFAULT_ORG
    ) -> Dict[str, Any]:
        spec.setdefault("id", policy_id)
        return self._create_or_update(
            f"{self._vpc_path(org, project, vpc_id)}/gateway-policies/{policy_id}", spec
        )

    # VPC NAT Rules

    def list_nat_rules(
        self, project: str, vpc_id: str, org: str = DEFAULT_ORG
    ) -> List[NATRule]:
        return self._list(
            f"{self._vpc_path(org, project, vpc_id)}/nat/nat-rules", NATRule
        )

    def create_or_update_nat_rule(
        self, project: str, vpc_id: str, rule_id: str,
        spec: Dict[str, Any], org: str = DEFAULT_ORG
    ) -> Dict[str, Any]:
        spec.setdefault("id", rule_id)
        return self._create_or_update(
            f"{self._vpc_path(org, project, vpc_id)}/nat/nat-rules/{rule_id}", spec
        )

    def delete_nat_rule(
        self, project: str, vpc_id: str, rule_id: str, org: str = DEFAULT_ORG
    ) -> None:
        self._delete(f"{self._vpc_path(org, project, vpc_id)}/nat/nat-rules/{rule_id}")

    # VPC Static Routes

    def list_static_routes(
        self, project: str, vpc_id: str, org: str = DEFAULT_ORG
    ) -> List[StaticRoute]:
        return self._list(
            f"{self._vpc_path(org, project, vpc_id)}/static-routes", StaticRoute
        )

    def create_or_update_static_route(
        self, project: str, vpc_id: str, route_id: str,
        spec: Dict[str, Any], org: str = DEFAULT_ORG
    ) -> Dict[str, Any]:
        spec.setdefault("id", route_id)
        return self._create_or_update(
            f"{self._vpc_path(org, project, vpc_id)}/static-routes/{route_id}", spec
        )

    def delete_static_route(
        self, project: str, vpc_id: str, route_id: str, org: str = DEFAULT_ORG
    ) -> None:
        self._delete(f"{self._vpc_path(org, project, vpc_id)}/static-routes/{route_id}")

    # VPC IP Address Allocations

    def list_ip_allocations(
        self, project: str, vpc_id: str, org: str = DEFAULT_ORG
    ) -> List[Dict[str, Any]]:
        return self._list(
            f"{self._vpc_path(org, project, vpc_id)}/ip-address-allocations", type(None)
        ) or []

    def create_or_update_ip_allocation(
        self, project: str, vpc_id: str, alloc_id: str,
        spec: Dict[str, Any], org: str = DEFAULT_ORG
    ) -> Dict[str, Any]:
        spec.setdefault("id", alloc_id)
        return self._create_or_update(
            f"{self._vpc_path(org, project, vpc_id)}/ip-address-allocations/{alloc_id}", spec
        )

    def delete_ip_allocation(
        self, project: str, vpc_id: str, alloc_id: str, org: str = DEFAULT_ORG
    ) -> None:
        self._delete(
            f"{self._vpc_path(org, project, vpc_id)}/ip-address-allocations/{alloc_id}"
        )

    # VPC DHCP Static Bindings

    def list_dhcp_bindings(
        self, project: str, vpc_id: str, subnet_id: str, org: str = DEFAULT_ORG
    ) -> List[Dict[str, Any]]:
        response = self._raw_get(
            f"{self._vpc_path(org, project, vpc_id)}/subnets/{subnet_id}"
            "/dhcp-static-binding-configs"
        )
        return response.get("results", [])

    def create_or_update_dhcp_binding(
        self, project: str, vpc_id: str, subnet_id: str, binding_id: str,
        spec: Dict[str, Any], org: str = DEFAULT_ORG
    ) -> Dict[str, Any]:
        spec.setdefault("id", binding_id)
        return self._create_or_update(
            f"{self._vpc_path(org, project, vpc_id)}/subnets/{subnet_id}"
            f"/dhcp-static-binding-configs/{binding_id}",
            spec,
        )

    def delete_dhcp_binding(
        self, project: str, vpc_id: str, subnet_id: str, binding_id: str,
        org: str = DEFAULT_ORG
    ) -> None:
        self._delete(
            f"{self._vpc_path(org, project, vpc_id)}/subnets/{subnet_id}"
            f"/dhcp-static-binding-configs/{binding_id}"
        )

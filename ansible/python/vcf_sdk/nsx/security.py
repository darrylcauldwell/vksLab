"""Security management (groups, firewall policies) for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx import Group, SecurityPolicy, FirewallRule, GatewayPolicy
from vcf_sdk.nsx.base import NSXBaseManager

DOMAIN = "default"


class GroupManager(NSXBaseManager):
    """Manage NSX-T security groups."""

    def list(self) -> List[Group]:
        return self._list(f"/infra/domains/{DOMAIN}/groups", Group)

    def get(self, group_id: str) -> Group:
        return self._get(f"/infra/domains/{DOMAIN}/groups/{group_id}", Group)

    def create_or_update(self, group_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", group_id)
        return self._create_or_update(f"/infra/domains/{DOMAIN}/groups/{group_id}", spec)

    def delete(self, group_id: str) -> None:
        self._delete(f"/infra/domains/{DOMAIN}/groups/{group_id}")


class SecurityPolicyManager(NSXBaseManager):
    """Manage NSX-T distributed firewall policies and rules."""

    def list(self) -> List[SecurityPolicy]:
        return self._list(f"/infra/domains/{DOMAIN}/security-policies", SecurityPolicy)

    def get(self, policy_id: str) -> SecurityPolicy:
        return self._get(
            f"/infra/domains/{DOMAIN}/security-policies/{policy_id}", SecurityPolicy
        )

    def create_or_update(self, policy_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", policy_id)
        return self._create_or_update(
            f"/infra/domains/{DOMAIN}/security-policies/{policy_id}", spec
        )

    def delete(self, policy_id: str) -> None:
        self._delete(f"/infra/domains/{DOMAIN}/security-policies/{policy_id}")

    # Individual rules

    def list_rules(self, policy_id: str) -> List[FirewallRule]:
        return self._list(
            f"/infra/domains/{DOMAIN}/security-policies/{policy_id}/rules",
            FirewallRule,
        )

    def get_rule(self, policy_id: str, rule_id: str) -> FirewallRule:
        return self._get(
            f"/infra/domains/{DOMAIN}/security-policies/{policy_id}/rules/{rule_id}",
            FirewallRule,
        )

    def create_or_update_rule(
        self, policy_id: str, rule_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", rule_id)
        return self._create_or_update(
            f"/infra/domains/{DOMAIN}/security-policies/{policy_id}/rules/{rule_id}", spec
        )

    def delete_rule(self, policy_id: str, rule_id: str) -> None:
        self._delete(
            f"/infra/domains/{DOMAIN}/security-policies/{policy_id}/rules/{rule_id}"
        )


class GatewayPolicyManager(NSXBaseManager):
    """Manage NSX-T gateway firewall policies."""

    def list(self) -> List[GatewayPolicy]:
        return self._list(f"/infra/domains/{DOMAIN}/gateway-policies", GatewayPolicy)

    def get(self, policy_id: str) -> GatewayPolicy:
        return self._get(
            f"/infra/domains/{DOMAIN}/gateway-policies/{policy_id}", GatewayPolicy
        )

    def create_or_update(self, policy_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", policy_id)
        return self._create_or_update(
            f"/infra/domains/{DOMAIN}/gateway-policies/{policy_id}", spec
        )

    def delete(self, policy_id: str) -> None:
        self._delete(f"/infra/domains/{DOMAIN}/gateway-policies/{policy_id}")

"""NAT rule management for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx import NATRule
from vcf_sdk.nsx.base import NSXBaseManager


class NATManager(NSXBaseManager):
    """Manage NAT rules on Tier-0 and Tier-1 gateways."""

    def _base_path(self, gateway_type: str, gateway_id: str, nat_id: str = "USER") -> str:
        return f"/infra/{gateway_type}/{gateway_id}/nat/{nat_id}/nat-rules"

    # Tier-0 NAT

    def list_tier0_rules(self, tier0_id: str, nat_id: str = "USER") -> List[NATRule]:
        return self._list(self._base_path("tier-0s", tier0_id, nat_id), NATRule)

    def get_tier0_rule(self, tier0_id: str, rule_id: str, nat_id: str = "USER") -> NATRule:
        return self._get(f"{self._base_path('tier-0s', tier0_id, nat_id)}/{rule_id}", NATRule)

    def create_or_update_tier0_rule(
        self, tier0_id: str, rule_id: str, spec: Dict[str, Any], nat_id: str = "USER"
    ) -> Dict[str, Any]:
        spec.setdefault("id", rule_id)
        return self._create_or_update(
            f"{self._base_path('tier-0s', tier0_id, nat_id)}/{rule_id}", spec
        )

    def delete_tier0_rule(self, tier0_id: str, rule_id: str, nat_id: str = "USER") -> None:
        self._delete(f"{self._base_path('tier-0s', tier0_id, nat_id)}/{rule_id}")

    # Tier-1 NAT

    def list_tier1_rules(self, tier1_id: str, nat_id: str = "USER") -> List[NATRule]:
        return self._list(self._base_path("tier-1s", tier1_id, nat_id), NATRule)

    def get_tier1_rule(self, tier1_id: str, rule_id: str, nat_id: str = "USER") -> NATRule:
        return self._get(f"{self._base_path('tier-1s', tier1_id, nat_id)}/{rule_id}", NATRule)

    def create_or_update_tier1_rule(
        self, tier1_id: str, rule_id: str, spec: Dict[str, Any], nat_id: str = "USER"
    ) -> Dict[str, Any]:
        spec.setdefault("id", rule_id)
        return self._create_or_update(
            f"{self._base_path('tier-1s', tier1_id, nat_id)}/{rule_id}", spec
        )

    def delete_tier1_rule(self, tier1_id: str, rule_id: str, nat_id: str = "USER") -> None:
        self._delete(f"{self._base_path('tier-1s', tier1_id, nat_id)}/{rule_id}")

"""DNS forwarder management for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx import DNSForwarderZone
from vcf_sdk.nsx.base import NSXBaseManager


class DNSManager(NSXBaseManager):
    """Manage DNS forwarder zones and gateway DNS forwarders."""

    # DNS Forwarder Zones

    def list_zones(self) -> List[DNSForwarderZone]:
        return self._list("/infra/dns-forwarder-zones", DNSForwarderZone)

    def get_zone(self, zone_id: str) -> DNSForwarderZone:
        return self._get(f"/infra/dns-forwarder-zones/{zone_id}", DNSForwarderZone)

    def create_or_update_zone(self, zone_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", zone_id)
        return self._create_or_update(f"/infra/dns-forwarder-zones/{zone_id}", spec)

    def delete_zone(self, zone_id: str) -> None:
        self._delete(f"/infra/dns-forwarder-zones/{zone_id}")

    # Gateway DNS Forwarders

    def get_tier0_forwarder(self, tier0_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/infra/tier-0s/{tier0_id}/dns-forwarder")

    def set_tier0_forwarder(self, tier0_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        return self._create_or_update(f"/infra/tier-0s/{tier0_id}/dns-forwarder", spec)

    def get_tier1_forwarder(self, tier1_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/infra/tier-1s/{tier1_id}/dns-forwarder")

    def set_tier1_forwarder(self, tier1_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        return self._create_or_update(f"/infra/tier-1s/{tier1_id}/dns-forwarder", spec)

"""EVPN management for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx.evpn import EVPNConfig, EVPNTenant, EVPNTunnelEndpoint
from vcf_sdk.nsx.base import NSXBaseManager


class EVPNManager(NSXBaseManager):
    """Manage EVPN configuration, tenants, and tunnel endpoints."""

    # EVPN Config (on Tier-0 locale service)

    def get_config(self, tier0_id: str, ls_id: str) -> EVPNConfig:
        return self._get(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/evpn", EVPNConfig
        )

    def set_config(
        self, tier0_id: str, ls_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._create_or_update(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/evpn", spec
        )

    # EVPN Tunnel Endpoints (on Tier-0 locale service)

    def list_tunnel_endpoints(self, tier0_id: str, ls_id: str) -> List[EVPNTunnelEndpoint]:
        return self._list(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/evpn/tunnel-endpoints",
            EVPNTunnelEndpoint,
        )

    def get_tunnel_endpoint(
        self, tier0_id: str, ls_id: str, ep_id: str
    ) -> EVPNTunnelEndpoint:
        return self._get(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/evpn/tunnel-endpoints/{ep_id}",
            EVPNTunnelEndpoint,
        )

    def create_or_update_tunnel_endpoint(
        self, tier0_id: str, ls_id: str, ep_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", ep_id)
        return self._create_or_update(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/evpn/tunnel-endpoints/{ep_id}",
            spec,
        )

    def delete_tunnel_endpoint(self, tier0_id: str, ls_id: str, ep_id: str) -> None:
        self._delete(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/evpn/tunnel-endpoints/{ep_id}"
        )

    # EVPN Tenants (global)

    def list_tenants(self) -> List[EVPNTenant]:
        return self._list("/infra/evpn-tenant-configs", EVPNTenant)

    def get_tenant(self, tenant_id: str) -> EVPNTenant:
        return self._get(f"/infra/evpn-tenant-configs/{tenant_id}", EVPNTenant)

    def create_or_update_tenant(
        self, tenant_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", tenant_id)
        return self._create_or_update(f"/infra/evpn-tenant-configs/{tenant_id}", spec)

    def delete_tenant(self, tenant_id: str) -> None:
        self._delete(f"/infra/evpn-tenant-configs/{tenant_id}")

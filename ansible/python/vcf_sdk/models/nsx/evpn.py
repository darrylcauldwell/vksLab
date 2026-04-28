"""EVPN models for NSX-T Policy API."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class EVPNConfig(NSXResource):
    """EVPN configuration on a Tier-0 gateway."""

    mode: Optional[str] = Field(default=None, description="INLINE or ROUTE_SERVER")
    encapsulation: Optional[str] = Field(default=None, description="VXLAN")


class EVPNTenant(NSXResource):
    """EVPN tenant configuration."""

    transport_vni: Optional[int] = Field(default=None)
    vni_pool_path: Optional[str] = Field(default=None)
    mappings: Optional[List[Dict[str, Any]]] = Field(default=None)


class EVPNTunnelEndpoint(NSXResource):
    """EVPN tunnel endpoint."""

    external_interface_path: Optional[str] = Field(default=None)

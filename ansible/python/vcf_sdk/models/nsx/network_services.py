"""Network service models (DHCP, DNS) for NSX-T Policy API."""

from typing import List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class DHCPServerConfig(NSXResource):
    """DHCP server configuration."""

    server_address: Optional[str] = Field(default=None)
    lease_time: Optional[int] = Field(default=None)
    edge_cluster_path: Optional[str] = Field(default=None)
    preferred_edge_paths: Optional[List[str]] = Field(default=None)


class DHCPRelayConfig(NSXResource):
    """DHCP relay configuration."""

    server_addresses: Optional[List[str]] = Field(default=None)


class DNSForwarderZone(NSXResource):
    """DNS forwarder zone."""

    dns_domain_names: Optional[List[str]] = Field(default=None)
    upstream_servers: Optional[List[str]] = Field(default=None)

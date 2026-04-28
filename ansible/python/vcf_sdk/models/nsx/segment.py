"""Segment models for NSX-T Policy API."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class SegmentSubnet(NSXResource):
    """Segment subnet configuration."""

    gateway_address: Optional[str] = Field(default=None)
    dhcp_ranges: Optional[List[str]] = Field(default=None)
    network: Optional[str] = Field(default=None)
    dhcp_config: Optional[Dict[str, Any]] = Field(default=None)


class Segment(NSXResource):
    """NSX-T overlay or VLAN segment."""

    transport_zone_path: Optional[str] = Field(default=None)
    connectivity_path: Optional[str] = Field(
        default=None, description="Path to Tier-0 or Tier-1 gateway"
    )
    subnets: Optional[List[SegmentSubnet]] = Field(default=None)
    vlan_ids: Optional[List[str]] = Field(default=None, description="VLAN IDs for VLAN segments")
    admin_state: Optional[str] = Field(default=None, description="UP or DOWN")
    replication_mode: Optional[str] = Field(default=None, description="MTEP or SOURCE")
    dhcp_config_path: Optional[str] = Field(default=None)
    overlay_id: Optional[int] = Field(default=None)

    @property
    def is_vlan(self) -> bool:
        return bool(self.vlan_ids)

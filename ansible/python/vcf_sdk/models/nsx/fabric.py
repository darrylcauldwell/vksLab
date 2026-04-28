"""Fabric models (transport zones, edge clusters) for NSX-T Policy API."""

from typing import Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class TransportZone(NSXResource):
    """NSX-T transport zone (read-only from Policy API)."""

    tz_type: Optional[str] = Field(
        default=None, description="OVERLAY_STANDARD, OVERLAY_ENS, or VLAN_BACKED"
    )
    is_default: Optional[bool] = Field(default=None)
    nsx_id: Optional[str] = Field(default=None)

    @property
    def is_overlay(self) -> bool:
        return self.tz_type is not None and self.tz_type.startswith("OVERLAY")

    @property
    def is_vlan(self) -> bool:
        return self.tz_type == "VLAN_BACKED"


class EdgeCluster(NSXResource):
    """NSX-T edge cluster (read-only from Policy API)."""

    nsx_id: Optional[str] = Field(default=None)
    member_node_type: Optional[str] = Field(default=None)
    deployment_type: Optional[str] = Field(default=None)


class EdgeNode(NSXResource):
    """NSX-T edge node within an edge cluster."""

    nsx_id: Optional[str] = Field(default=None)

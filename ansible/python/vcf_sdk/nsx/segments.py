"""Segment management for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx import Segment, SegmentPort
from vcf_sdk.nsx.base import NSXBaseManager


class SegmentManager(NSXBaseManager):
    """Manage NSX-T segments (overlay and VLAN)."""

    def list(self) -> List[Segment]:
        """List all infra-level segments."""
        return self._list("/infra/segments", Segment)

    def get(self, segment_id: str) -> Segment:
        """Get segment by ID."""
        return self._get(f"/infra/segments/{segment_id}", Segment)

    def create_or_update(self, segment_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a segment (PATCH — idempotent)."""
        spec.setdefault("id", segment_id)
        return self._create_or_update(f"/infra/segments/{segment_id}", spec)

    def delete(self, segment_id: str) -> None:
        """Delete a segment."""
        self._delete(f"/infra/segments/{segment_id}")

    # Tier-1 connected segments

    def list_tier1_segments(self, tier1_id: str) -> List[Segment]:
        """List segments connected to a Tier-1 gateway."""
        return self._list(f"/infra/tier-1s/{tier1_id}/segments", Segment)

    def get_tier1_segment(self, tier1_id: str, segment_id: str) -> Segment:
        """Get a Tier-1 connected segment."""
        return self._get(f"/infra/tier-1s/{tier1_id}/segments/{segment_id}", Segment)

    def create_or_update_tier1_segment(
        self, tier1_id: str, segment_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create or update a Tier-1 connected segment."""
        spec.setdefault("id", segment_id)
        return self._create_or_update(
            f"/infra/tier-1s/{tier1_id}/segments/{segment_id}", spec
        )

    def delete_tier1_segment(self, tier1_id: str, segment_id: str) -> None:
        """Delete a Tier-1 connected segment."""
        self._delete(f"/infra/tier-1s/{tier1_id}/segments/{segment_id}")

    # Segment Ports

    def list_ports(self, segment_id: str) -> List[SegmentPort]:
        """List all ports on a segment."""
        return self._list(f"/infra/segments/{segment_id}/ports", SegmentPort)

    def get_port(self, segment_id: str, port_id: str) -> SegmentPort:
        return self._get(f"/infra/segments/{segment_id}/ports/{port_id}", SegmentPort)

    def create_or_update_port(
        self, segment_id: str, port_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", port_id)
        return self._create_or_update(f"/infra/segments/{segment_id}/ports/{port_id}", spec)

    def delete_port(self, segment_id: str, port_id: str) -> None:
        self._delete(f"/infra/segments/{segment_id}/ports/{port_id}")

"""VM snapshot management for vCenter REST API."""

from typing import Any, Dict, List

from vcf_sdk.models.vcenter.advanced import Snapshot
from vcf_sdk.vcenter.base import VCBaseManager


class SnapshotManager(VCBaseManager):
    """Manage VM snapshots."""

    def list(self, vm_id: str) -> List[Snapshot]:
        """List snapshots for a VM."""
        response = self._raw_get(f"/vcenter/vm/{vm_id}/snapshot")
        items = response if isinstance(response, list) else response.get("items", [])
        return [Snapshot(**s) for s in items]

    def get(self, vm_id: str, snapshot_id: str) -> Snapshot:
        return self._get(f"/vcenter/vm/{vm_id}/snapshot/{snapshot_id}", Snapshot)

    def create(self, vm_id: str, spec: Dict[str, Any]) -> str:
        """Create a snapshot. Returns snapshot identifier."""
        return self._post(f"/vcenter/vm/{vm_id}/snapshot", data=spec)

    def delete(self, vm_id: str, snapshot_id: str) -> None:
        self._delete(f"/vcenter/vm/{vm_id}/snapshot/{snapshot_id}")

    def revert(self, vm_id: str, snapshot_id: str) -> None:
        """Revert VM to a snapshot."""
        self._post(f"/vcenter/vm/{vm_id}/snapshot/{snapshot_id}?action=revert")

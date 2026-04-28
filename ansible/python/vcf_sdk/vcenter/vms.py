"""VM lifecycle management for vCenter REST API."""

from typing import Any, Dict, List

from vcf_sdk.models.vcenter import VM, VMDetail
from vcf_sdk.vcenter.base import VCBaseManager


class VMManager(VCBaseManager):
    """VM lifecycle: list, get, create, delete, power operations."""

    def list(self, **filters) -> List[VM]:
        """
        List VMs.

        Supported filters: names, power_states, hosts, clusters,
        datacenters, folders, resource_pools (as filter.X query params)
        """
        params = {f"filter.{k}": v for k, v in filters.items() if v is not None}
        return self._list("/vcenter/vm", VM, **params)

    def get(self, vm_id: str) -> VMDetail:
        """Get detailed VM info."""
        return self._get(f"/vcenter/vm/{vm_id}", VMDetail)

    def create(self, spec: Dict[str, Any]) -> str:
        """
        Create a VM.

        Returns:
            VM identifier string (e.g., "vm-42")
        """
        return self._post("/vcenter/vm", data=spec)

    def delete(self, vm_id: str) -> None:
        """Delete a VM."""
        self._delete(f"/vcenter/vm/{vm_id}")

    # Power operations

    def power_on(self, vm_id: str) -> None:
        """Power on a VM."""
        self._post(f"/vcenter/vm/{vm_id}/power?action=start")

    def power_off(self, vm_id: str) -> None:
        """Power off a VM (hard stop)."""
        self._post(f"/vcenter/vm/{vm_id}/power?action=stop")

    def suspend(self, vm_id: str) -> None:
        """Suspend a VM."""
        self._post(f"/vcenter/vm/{vm_id}/power?action=suspend")

    def reset(self, vm_id: str) -> None:
        """Reset a VM."""
        self._post(f"/vcenter/vm/{vm_id}/power?action=reset")

    def get_power_state(self, vm_id: str) -> Dict[str, Any]:
        """Get VM power state."""
        return self._raw_get(f"/vcenter/vm/{vm_id}/power")

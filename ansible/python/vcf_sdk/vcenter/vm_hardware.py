"""VM hardware management (disks, NICs, CD-ROMs) for vCenter REST API."""

from typing import Any, Dict, List

from vcf_sdk.vcenter.base import VCBaseManager


class VMHardwareManager(VCBaseManager):
    """Manage VM hardware — disks, NICs, CD-ROMs."""

    # Disks

    def list_disks(self, vm_id: str) -> List[Dict[str, Any]]:
        response = self._raw_get(f"/vcenter/vm/{vm_id}/hardware/disk")
        return response if isinstance(response, list) else []

    def get_disk(self, vm_id: str, disk_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/vm/{vm_id}/hardware/disk/{disk_id}")

    def create_disk(self, vm_id: str, spec: Dict[str, Any]) -> str:
        """Add a disk to a VM. Returns disk identifier."""
        return self._post(f"/vcenter/vm/{vm_id}/hardware/disk", data=spec)

    def update_disk(self, vm_id: str, disk_id: str, spec: Dict[str, Any]) -> None:
        self._patch(f"/vcenter/vm/{vm_id}/hardware/disk/{disk_id}", data=spec)

    def delete_disk(self, vm_id: str, disk_id: str) -> None:
        self._delete(f"/vcenter/vm/{vm_id}/hardware/disk/{disk_id}")

    # NICs

    def list_nics(self, vm_id: str) -> List[Dict[str, Any]]:
        response = self._raw_get(f"/vcenter/vm/{vm_id}/hardware/ethernet")
        return response if isinstance(response, list) else []

    def get_nic(self, vm_id: str, nic_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/vm/{vm_id}/hardware/ethernet/{nic_id}")

    def create_nic(self, vm_id: str, spec: Dict[str, Any]) -> str:
        """Add a NIC to a VM. Returns NIC identifier."""
        return self._post(f"/vcenter/vm/{vm_id}/hardware/ethernet", data=spec)

    def update_nic(self, vm_id: str, nic_id: str, spec: Dict[str, Any]) -> None:
        self._patch(f"/vcenter/vm/{vm_id}/hardware/ethernet/{nic_id}", data=spec)

    def delete_nic(self, vm_id: str, nic_id: str) -> None:
        self._delete(f"/vcenter/vm/{vm_id}/hardware/ethernet/{nic_id}")

    def connect_nic(self, vm_id: str, nic_id: str) -> None:
        self._post(f"/vcenter/vm/{vm_id}/hardware/ethernet/{nic_id}?action=connect")

    def disconnect_nic(self, vm_id: str, nic_id: str) -> None:
        self._post(f"/vcenter/vm/{vm_id}/hardware/ethernet/{nic_id}?action=disconnect")

    # CD-ROMs

    def list_cdroms(self, vm_id: str) -> List[Dict[str, Any]]:
        response = self._raw_get(f"/vcenter/vm/{vm_id}/hardware/cdrom")
        return response if isinstance(response, list) else []

    def get_cdrom(self, vm_id: str, cdrom_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/vm/{vm_id}/hardware/cdrom/{cdrom_id}")

    def create_cdrom(self, vm_id: str, spec: Dict[str, Any]) -> str:
        return self._post(f"/vcenter/vm/{vm_id}/hardware/cdrom", data=spec)

    def delete_cdrom(self, vm_id: str, cdrom_id: str) -> None:
        self._delete(f"/vcenter/vm/{vm_id}/hardware/cdrom/{cdrom_id}")

    # Boot config

    def get_boot(self, vm_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/vm/{vm_id}/hardware/boot")

    def update_boot(self, vm_id: str, spec: Dict[str, Any]) -> None:
        self._patch(f"/vcenter/vm/{vm_id}/hardware/boot", data=spec)

    # CPU

    def get_cpu(self, vm_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/vm/{vm_id}/hardware/cpu")

    def update_cpu(self, vm_id: str, spec: Dict[str, Any]) -> None:
        self._patch(f"/vcenter/vm/{vm_id}/hardware/cpu", data=spec)

    # Memory

    def get_memory(self, vm_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/vm/{vm_id}/hardware/memory")

    def update_memory(self, vm_id: str, spec: Dict[str, Any]) -> None:
        self._patch(f"/vcenter/vm/{vm_id}/hardware/memory", data=spec)

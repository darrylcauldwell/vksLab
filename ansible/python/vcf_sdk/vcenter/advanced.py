"""Advanced vCenter operations — DRS, folders, guest customization, permissions."""

from typing import Any, Dict, List

from vcf_sdk.models.vcenter.advanced import DRSRule, Folder
from vcf_sdk.vcenter.base import VCBaseManager


class DRSRuleManager(VCBaseManager):
    """Manage DRS affinity/anti-affinity rules on clusters."""

    def list(self, cluster_id: str) -> List[DRSRule]:
        """List DRS rules for a cluster."""
        # DRS rules are available under cluster configuration
        response = self._raw_get(f"/vcenter/cluster/{cluster_id}")
        # Extract rules if present in cluster detail
        if isinstance(response, dict):
            rules = response.get("drs_rules", [])
            return [DRSRule(**r) for r in rules]
        return []


class FolderManager(VCBaseManager):
    """Manage vCenter folders."""

    def list(self, **filters) -> List[Folder]:
        """List folders. Filters: names, type, datacenters, parent_folders."""
        params = {f"filter.{k}": v for k, v in filters.items() if v is not None}
        return self._list("/vcenter/folder", Folder, **params)

    def get(self, folder_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/folder/{folder_id}")

    def create(self, spec: Dict[str, Any]) -> str:
        """Create a folder. Returns folder identifier."""
        return self._post("/vcenter/folder", data=spec)

    def delete(self, folder_id: str) -> None:
        self._delete(f"/vcenter/folder/{folder_id}")


class GuestCustomizationManager(VCBaseManager):
    """VM guest customization specs."""

    def list(self) -> List[Dict[str, Any]]:
        response = self._raw_get("/vcenter/guest/customization-specs")
        return response if isinstance(response, list) else []

    def get(self, spec_name: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/guest/customization-specs/{spec_name}")

    def create(self, spec: Dict[str, Any]) -> str:
        return self._post("/vcenter/guest/customization-specs", data=spec)

    def set(self, spec_name: str, spec: Dict[str, Any]) -> None:
        self._put(f"/vcenter/guest/customization-specs/{spec_name}", data=spec)

    def delete(self, spec_name: str) -> None:
        self._delete(f"/vcenter/guest/customization-specs/{spec_name}")

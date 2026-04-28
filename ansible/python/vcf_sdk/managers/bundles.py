"""Bundle and upgrade management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import Bundle, Upgradable, Upgrade

logger = logging.getLogger(__name__)


class BundleManager(BaseManager):
    """Lifecycle bundle and upgrade management."""

    # Bundles

    def list(self) -> List[Bundle]:
        """List available bundles."""
        response = self._get("/v1/bundles")
        return [Bundle(**b) for b in response.get("elements", [])]

    def get(self, bundle_id: str) -> Bundle:
        """Get bundle by ID."""
        response = self._get(f"/v1/bundles/{bundle_id}")
        return Bundle(**response)

    def download(self, bundle_id: str) -> Bundle:
        """Request bundle download."""
        response = self._patch(f"/v1/bundles/{bundle_id}", data={"bundleDownloadSpec": {"downloadNow": True}})
        return Bundle(**response)

    def upload(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a bundle to SDDC Manager."""
        return self._post("/v1/bundles", data=spec)

    # Upgradables

    def list_upgradables(self) -> List[Upgradable]:
        """List upgradable resources."""
        response = self._get("/v1/system/upgradables")
        return [Upgradable(**u) for u in response.get("elements", [])]

    # Upgrades

    def list_upgrades(self) -> List[Upgrade]:
        """List upgrade operations."""
        response = self._get("/v1/upgrades")
        return [Upgrade(**u) for u in response.get("elements", [])]

    def get_upgrade(self, upgrade_id: str) -> Upgrade:
        """Get upgrade status."""
        response = self._get(f"/v1/upgrades/{upgrade_id}")
        return Upgrade(**response)

    def start_upgrade(self, spec: Dict[str, Any]) -> Upgrade:
        """Start an upgrade."""
        response = self._post("/v1/upgrades", data=spec)
        return Upgrade(**response)

    def schedule_upgrade(self, upgrade_id: str) -> Upgrade:
        """Change DRAFT upgrade to SCHEDULED."""
        response = self._patch(f"/v1/upgrades/{upgrade_id}")
        return Upgrade(**response)

    def start_upgrade_precheck(self, upgrade_id: str) -> Dict[str, Any]:
        """Start an upgrade precheck."""
        return self._post(f"/v1/upgrades/{upgrade_id}/prechecks")

    def get_upgrade_precheck(self, upgrade_id: str, precheck_id: str) -> Dict[str, Any]:
        """Get upgrade precheck task."""
        return self._get(f"/v1/upgrades/{upgrade_id}/prechecks/{precheck_id}")

    def preview_upgrade(self, **filters) -> Dict[str, Any]:
        """Preview upgrade for a domain."""
        params = [f"{k}={v}" for k, v in filters.items() if v is not None]
        endpoint = "/v1/upgrades/preview"
        if params:
            endpoint += "?" + "&".join(params)
        return self._get(endpoint)

    # Domain-scoped upgradables

    def get_domain_upgradables(self, domain_id: str) -> Dict[str, Any]:
        """Get upgradable resources for a domain."""
        return self._get(f"/v1/upgradables/domains/{domain_id}")

    def get_domain_nsxt_upgradables(self, domain_id: str) -> Dict[str, Any]:
        """Get upgradable NSX resources for a domain."""
        return self._get(f"/v1/upgradables/domains/{domain_id}/nsxt")

    def get_domain_cluster_upgradables(self, domain_id: str) -> Dict[str, Any]:
        """Get upgradable cluster packages for a domain."""
        return self._get(f"/v1/upgradables/domains/{domain_id}/clusters")

    def get_sddc_manager_upgradables(self) -> Dict[str, Any]:
        """Get SDDC Manager upgradables."""
        return self._get("/v1/sddc-manager/upgradables")

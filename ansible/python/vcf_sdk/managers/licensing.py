"""License management."""

import logging
from typing import Any, Dict, List, Optional

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import LicenseKey

logger = logging.getLogger(__name__)


class LicenseManager(BaseManager):
    """License key management."""

    def list(
        self,
        product_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[LicenseKey]:
        """
        List license keys.

        Args:
            product_type: Filter by type (VCENTER, ESXI, VSAN, NSXT)
            status: Filter by status (ACTIVE, EXPIRED)
        """
        params = []
        if product_type:
            params.append(f"productType={product_type}")
        if status:
            params.append(f"licenseKeyStatus={status}")
        endpoint = "/v1/license-keys"
        if params:
            endpoint += "?" + "&".join(params)
        response = self._get(endpoint)
        return [LicenseKey(**k) for k in response.get("elements", [])]

    def add(self, spec: Dict[str, Any]) -> LicenseKey:
        """Add a license key."""
        response = self._post("/v1/license-keys", data=spec)
        return LicenseKey(**response)

    def remove(self, key: str) -> None:
        """Remove a license key."""
        self._delete(f"/v1/license-keys/{key}")

    def update(self, key_or_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update a license key."""
        return self._patch(f"/v1/license-keys/{key_or_id}", data=spec)

    def get_licensing_info(self) -> Dict[str, Any]:
        """Get licensing mode information."""
        return self._get("/v1/licensing-info")

    def get_system_licensing(self) -> Dict[str, Any]:
        """Get system licensing info."""
        return self._get("/v1/licensing-info/system")

    def get_domain_licensing(self, domain_id: str) -> Dict[str, Any]:
        """Get domain licensing info."""
        return self._get(f"/v1/licensing-info/domains/{domain_id}")

    def get_product_types(self) -> Dict[str, Any]:
        """Get license product types."""
        return self._get("/v1/license-keys/product-types")

    def set_resource_license(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Set license key for a resource."""
        return self._put("/v1/resources/licensing-infos", data=spec)

    def start_license_check(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Start license check by resource."""
        return self._post("/v1/resources/license-checks", data=spec)

    def get_license_check(self, check_id: str) -> Dict[str, Any]:
        """Get license check result."""
        return self._get(f"/v1/resources/license-checks/{check_id}")

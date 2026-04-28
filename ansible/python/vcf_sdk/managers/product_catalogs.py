"""Product binaries and version catalog management."""

import logging
from typing import Any, Dict

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class ProductBinaryManager(BaseManager):
    """Product binary upload."""

    def upload(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a product binary."""
        return self._post("/v1/product-binaries", data=spec)


class ProductVersionCatalogManager(BaseManager):
    """Product version catalog management."""

    def get(self) -> Dict[str, Any]:
        """Get product version catalog content."""
        return self._get("/v1/product-version-catalogs")

    def upload(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Upload product version catalog with signature."""
        return self._post("/v1/product-version-catalogs", data=spec)

    def update_patches(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update product version catalog patches."""
        return self._patch("/v1/product-version-catalogs", data=spec)

    def get_upload_task(self, task_id: str) -> Dict[str, Any]:
        """Get catalog upload task status."""
        return self._get(f"/v1/product-version-catalogs/upload-tasks/{task_id}")

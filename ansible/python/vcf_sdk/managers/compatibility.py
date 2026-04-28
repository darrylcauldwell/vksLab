"""Compatibility matrix management."""

import logging
from typing import Any, Dict

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class CompatibilityManager(BaseManager):
    """Hardware/software compatibility matrix management."""

    def list(self) -> Dict[str, Any]:
        """Get compatibility matrices."""
        return self._get("/v1/compatibility-matrices")

    def update(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update compatibility matrix."""
        return self._put("/v1/compatibility-matrices", data=spec)

    def get_by_source(self, source: str) -> Dict[str, Any]:
        """Get compatibility matrix by source."""
        return self._get(f"/v1/compatibility-matrices/{source}")

    def get_metadata(self, source: str) -> Dict[str, Any]:
        """Get compatibility matrix metadata."""
        return self._get(f"/v1/compatibility-matrices/{source}/metadata")

    def get_content(self, source: str) -> Dict[str, Any]:
        """Get compatibility matrix content."""
        return self._get(f"/v1/compatibility-matrices/{source}/content")

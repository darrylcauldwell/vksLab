"""Version alias management."""

import logging
from typing import Any, Dict

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class VersionAliasManager(BaseManager):
    """Bundle component version alias management."""

    def get(self) -> Dict[str, Any]:
        """Get version alias configuration."""
        return self._get("/v1/system/settings/version-aliases")

    def update(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update version alias configurations."""
        return self._put("/v1/system/settings/version-aliases", data=spec)

    def update_specific(
        self, component_type: str, version: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update specific version alias."""
        return self._put(
            f"/v1/system/settings/version-aliases/{component_type}/{version}", data=spec
        )

    def delete_by_version(self, component_type: str, version: str) -> None:
        """Delete version alias by component type and version."""
        self._delete(f"/v1/system/settings/version-aliases/{component_type}/{version}")

    def delete_by_type(self, component_type: str) -> None:
        """Delete all aliases for a component type."""
        self._delete(f"/v1/system/settings/version-aliases/{component_type}")

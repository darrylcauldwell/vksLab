"""Resource functionalities management."""

import logging
from typing import Any, Dict

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class ResourceFunctionalityManager(BaseManager):
    """Resource functionalities and warnings."""

    # Functionalities

    def get(self) -> Dict[str, Any]:
        """Get resource functionalities."""
        return self._get("/v1/resource-functionalities")

    def update(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update resource functionalities."""
        return self._patch("/v1/resource-functionalities", data=spec)

    def get_global(self) -> Dict[str, Any]:
        """Get global resource functionalities setting."""
        return self._get("/v1/resource-functionalities/global")

    def update_global(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update global resource functionalities."""
        return self._patch("/v1/resource-functionalities/global", data=spec)

    # Warnings

    def list_warnings(self) -> Dict[str, Any]:
        """Get resource warnings."""
        return self._get("/v1/resource-warnings")

    def create_warning(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create a resource warning."""
        return self._post("/v1/resource-warnings", data=spec)

    def get_warning(self, warning_id: str) -> Dict[str, Any]:
        """Get resource warning by ID."""
        return self._get(f"/v1/resource-warnings/{warning_id}")

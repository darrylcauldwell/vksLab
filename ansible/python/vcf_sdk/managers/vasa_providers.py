"""VASA Provider management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class VASAProviderManager(BaseManager):
    """VASA Provider (vVols storage) management."""

    def list(self) -> List[Dict[str, Any]]:
        """List VASA providers."""
        response = self._get("/v1/vasa-providers")
        return response.get("elements", [])

    def get(self, provider_id: str) -> Dict[str, Any]:
        """Get VASA provider by ID."""
        return self._get(f"/v1/vasa-providers/{provider_id}")

    def create(self, spec: Dict[str, Any], validate: bool = True) -> Dict[str, Any]:
        """Create a VASA provider."""
        if validate:
            self._validate_and_wait("/v1/vasa-providers/validations", spec)
        return self._post("/v1/vasa-providers", data=spec)

    def update(self, provider_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update a VASA provider."""
        return self._patch(f"/v1/vasa-providers/{provider_id}", data=spec)

    def delete(self, provider_id: str) -> None:
        """Delete a VASA provider."""
        self._delete(f"/v1/vasa-providers/{provider_id}")

    def validate(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate VASA provider spec."""
        return self._post("/v1/vasa-providers/validations", data=spec)

    def get_validation(self, validation_id: str) -> Dict[str, Any]:
        """Get VASA provider validation status."""
        return self._get(f"/v1/vasa-providers/validations/{validation_id}")

    # Storage Containers

    def list_containers(self, provider_id: str) -> List[Dict[str, Any]]:
        """List storage containers for a VASA provider."""
        response = self._get(f"/v1/vasa-providers/{provider_id}/storage-containers")
        return response.get("elements", [])

    def add_containers(self, provider_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Add storage containers to a VASA provider."""
        return self._post(f"/v1/vasa-providers/{provider_id}/storage-containers", data=spec)

    def update_container(
        self, provider_id: str, container_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a storage container."""
        return self._patch(
            f"/v1/vasa-providers/{provider_id}/storage-containers/{container_id}", data=spec
        )

    def delete_container(self, provider_id: str, container_id: str) -> None:
        """Delete a storage container."""
        self._delete(f"/v1/vasa-providers/{provider_id}/storage-containers/{container_id}")

    # Users

    def list_users(self, provider_id: str) -> List[Dict[str, Any]]:
        """List VASA provider users."""
        response = self._get(f"/v1/vasa-providers/{provider_id}/users")
        return response.get("elements", [])

    def add_users(self, provider_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Add users to a VASA provider."""
        return self._post(f"/v1/vasa-providers/{provider_id}/users", data=spec)

    def update_user(
        self, provider_id: str, user_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a VASA provider user."""
        return self._patch(f"/v1/vasa-providers/{provider_id}/users/{user_id}", data=spec)

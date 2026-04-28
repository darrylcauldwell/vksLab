"""Credential management."""

import logging
from typing import Any, Dict, List, Optional

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import Credential, CredentialTask

logger = logging.getLogger(__name__)


class CredentialManager(BaseManager):
    """Credential rotation and management."""

    def list(
        self,
        resource_name: Optional[str] = None,
        resource_type: Optional[str] = None,
        account_type: Optional[str] = None,
    ) -> List[Credential]:
        """
        List credentials, optionally filtered.

        Args:
            resource_name: Filter by resource name (e.g., FQDN)
            resource_type: Filter by type (VCENTER, ESXI, NSXT_MANAGER, etc.)
            account_type: Filter by account type (USER, SYSTEM, SERVICE)
        """
        params = []
        if resource_name:
            params.append(f"resourceName={resource_name}")
        if resource_type:
            params.append(f"resourceType={resource_type}")
        if account_type:
            params.append(f"accountType={account_type}")
        endpoint = "/v1/credentials"
        if params:
            endpoint += "?" + "&".join(params)
        response = self._get(endpoint)
        return [Credential(**c) for c in response.get("elements", [])]

    def get(self, credential_id: str) -> Credential:
        """Get credential by ID."""
        response = self._get(f"/v1/credentials/{credential_id}")
        return Credential(**response)

    def update(self, spec: Dict[str, Any]) -> CredentialTask:
        """
        Update or rotate credentials.

        Args:
            spec: Credential update spec with operation type (UPDATE, ROTATE)
        """
        response = self._patch("/v1/credentials", data=spec)
        return CredentialTask(**response)

    def set_auto_rotate_policy(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Set credential auto-rotation policy."""
        return self._put("/v1/credentials/auto-rotate-policy", data=spec)

    def list_tasks(self) -> List[CredentialTask]:
        """List credential operation tasks."""
        response = self._get("/v1/credentials/tasks")
        return [CredentialTask(**t) for t in response.get("elements", [])]

    def get_task(self, task_id: str) -> CredentialTask:
        """Get credential task status."""
        response = self._get(f"/v1/credentials/tasks/{task_id}")
        return CredentialTask(**response)

    def cancel_task(self, task_id: str) -> None:
        """Cancel a credential task."""
        self._delete(f"/v1/credentials/tasks/{task_id}")

    def retry_task(self, task_id: str) -> CredentialTask:
        """Retry a failed credential task."""
        response = self._patch(f"/v1/credentials/tasks/{task_id}")
        return CredentialTask(**response)

    def get_expiry_details(self) -> Dict[str, Any]:
        """Get credential expiry information."""
        return self._get("/v1/credentials/ui")

"""SDDC Federation management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import Federation, FederationMember, Task

logger = logging.getLogger(__name__)


class FederationManager(BaseManager):
    """SDDC Federation (multi-site) management."""

    def get(self) -> Federation:
        """Get federation configuration."""
        response = self._get("/v1/sddc-federation")
        return Federation(**response)

    def configure(self, spec: Dict[str, Any]) -> Federation:
        """Configure federation."""
        response = self._put("/v1/sddc-federation", data=spec)
        return Federation(**response)

    def remove(self) -> None:
        """Remove federation configuration."""
        self._delete("/v1/sddc-federation")

    def list_members(self) -> List[FederationMember]:
        """List federation members."""
        response = self._get("/v1/sddc-federation/members")
        return [FederationMember(**m) for m in response.get("elements", [])]

    def join(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Join a federation."""
        return self._post("/v1/sddc-federation/members", data=spec)

    def create_invite_token(self) -> Dict[str, Any]:
        """Create a membership invitation token."""
        return self._post("/v1/sddc-federation/membership-tokens")

    def get_task(self, task_id: str) -> Task:
        """Get federation task status."""
        response = self._get(f"/v1/sddc-federation/tasks/{task_id}")
        return Task(**response)

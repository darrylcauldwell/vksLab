"""User and role management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import User, Role

logger = logging.getLogger(__name__)


class UserManager(BaseManager):
    """User and role management."""

    def list(self) -> List[User]:
        """List all users."""
        response = self._get("/v1/users")
        return [User(**u) for u in response.get("elements", [])]

    def create(self, spec: Dict[str, Any]) -> User:
        """Create a user."""
        response = self._post("/v1/users", data=spec)
        return User(**response)

    def create_service_user(self, spec: Dict[str, Any]) -> User:
        """Create a service user."""
        response = self._post("/v1/users", data={**spec, "type": "SERVICE"})
        return User(**response)

    def create_group(self, name: str, domain: str, role: str) -> Dict[str, Any]:
        """
        Add a group with a specified role.

        Args:
            name: Group name
            domain: Authentication domain (e.g., rainpole.io)
            role: Role name — ADMIN, OPERATOR, or VIEWER
        """
        # Look up role ID
        roles = self.list_roles()
        role_id = None
        for r in roles:
            if r.name == role:
                role_id = r.id
                break
        if not role_id:
            raise ValueError(f"Role '{role}' not found. Available: {[r.name for r in roles]}")

        spec = [{
            "name": name,
            "domain": domain.upper(),
            "type": "GROUP",
            "role": {"id": role_id},
        }]
        response = self._post("/v1/users", data=spec)
        return response

    def delete(self, user_id: str) -> None:
        """Delete a user."""
        self._delete(f"/v1/users/{user_id}")

    def list_roles(self) -> List[Role]:
        """List available roles."""
        response = self._get("/v1/roles")
        return [Role(**r) for r in response.get("elements", [])]

    # Local admin account

    def get_local_admin(self) -> Dict[str, Any]:
        """Get local admin account details."""
        return self._get("/v1/users/local/admin")

    def disable_local_admin(self) -> None:
        """Disable local admin account."""
        self._delete("/v1/users/local/admin")

    def update_local_admin_password(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update local admin account password."""
        return self._patch("/v1/users/local/admin", data=spec)

    def list_ui_users(self) -> Dict[str, Any]:
        """Get users assigned via SDDC Manager UI."""
        return self._get("/v1/users/ui")

    # SSO Domains

    def list_sso_domains(self) -> Dict[str, Any]:
        """Get SSO domains."""
        return self._get("/v1/sso-domains")

    def list_sso_entities(self, sso_domain: str) -> Dict[str, Any]:
        """Get users/groups from an SSO domain."""
        return self._get(f"/v1/sso-domains/{sso_domain}/entities")

"""Identity Provider and Identity Source management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class IdentityProviderManager(BaseManager):
    """Identity Provider and Identity Source management.

    VCF supports two types:
    - Embedded (LDAP/AD identity sources added to the embedded provider)
    - Microsoft ADFS (external identity provider)
    """

    # Identity Providers

    def list(self) -> List[Dict[str, Any]]:
        """List all identity providers."""
        response = self._get("/v1/identity-providers")
        return response.get("elements", [])

    def get(self, provider_id: str) -> Dict[str, Any]:
        """Get identity provider by ID."""
        return self._get(f"/v1/identity-providers/{provider_id}")

    def create(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an external identity provider (e.g., Microsoft ADFS).

        Args:
            spec: Identity provider spec (JSON)
        """
        return self._post("/v1/identity-providers", data=spec)

    def update(self, provider_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an external identity provider.

        Args:
            provider_id: Identity provider UUID
            spec: Updated spec
        """
        return self._patch(f"/v1/identity-providers/{provider_id}", data=spec)

    def delete(self, provider_id: str) -> None:
        """Delete an external identity provider (Microsoft ADFS)."""
        self._delete(f"/v1/identity-providers/{provider_id}")

    # Identity Sources (Embedded provider)

    def add_identity_source(
        self, provider_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add an identity source (LDAP/AD) to an embedded identity provider.

        Args:
            provider_id: Embedded identity provider UUID
            spec: Identity source spec with domain, LDAP connection details
        """
        return self._post(
            f"/v1/identity-providers/{provider_id}/identity-sources", data=spec
        )

    def update_identity_source(
        self, provider_id: str, domain_name: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an identity source.

        Args:
            provider_id: Embedded identity provider UUID
            domain_name: Domain name of the identity source
            spec: Updated identity source spec
        """
        return self._patch(
            f"/v1/identity-providers/{provider_id}/identity-sources/{domain_name}",
            data=spec,
        )

    def remove_identity_source(self, provider_id: str, domain_name: str) -> None:
        """
        Remove an identity source from an embedded identity provider.

        Args:
            provider_id: Embedded identity provider UUID
            domain_name: Domain name of the identity source to remove
        """
        self._delete(
            f"/v1/identity-providers/{provider_id}/identity-sources/{domain_name}"
        )

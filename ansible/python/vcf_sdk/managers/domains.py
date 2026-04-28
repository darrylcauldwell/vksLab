"""Workload domain management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import Domain, Task, Validation

logger = logging.getLogger(__name__)


class DomainManager(BaseManager):
    """Workload domain creation and management."""

    def list(self) -> List[Domain]:
        """List all domains."""
        response = self._get("/v1/domains")
        return [Domain(**d) for d in response.get("elements", [])]

    def get(self, domain_id: str) -> Domain:
        """Get domain by ID."""
        response = self._get(f"/v1/domains/{domain_id}")
        return Domain(**response)

    def create(self, spec: Dict[str, Any], validate: bool = True) -> Task:
        """
        Create a workload domain.

        Args:
            spec: Domain creation spec (JSON)
            validate: If True, validate before creating
        """
        if validate:
            self._validate_and_wait("/v1/domains/validations", spec)

        response = self._post("/v1/domains", data=spec)
        task_id = response.get("id")
        logger.info(f"Creating domain, task ID: {task_id}")
        return Task(**self._get(f"/v1/tasks/{task_id}"))

    def delete(self, domain_id: str) -> Task:
        """Delete a workload domain."""
        response = self._delete(f"/v1/domains/{domain_id}")
        task_id = response.get("id")
        return Task(**self._get(f"/v1/tasks/{task_id}"))

    def mark_for_deletion(self, domain_id: str) -> None:
        """Mark a domain for deletion."""
        self._patch(f"/v1/domains/{domain_id}", data={"markForDeletion": True})

    def get_endpoints(self, domain_id: str) -> Dict[str, Any]:
        """Get domain endpoints (vCenter, NSX, etc.)."""
        return self._get(f"/v1/domains/{domain_id}/endpoints")

    def validate(self, spec: Dict[str, Any]) -> Validation:
        """Validate domain creation spec."""
        response = self._post("/v1/domains/validations", data=spec)
        return Validation(**response)

    # Tags

    def get_tags(self, domain_id: str) -> Dict[str, Any]:
        """Get tags assigned to a domain."""
        return self._get(f"/v1/domains/{domain_id}/tags")

    def set_tags(self, domain_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Set tags on a domain."""
        return self._put(f"/v1/domains/{domain_id}/tags", data=spec)

    def delete_tags(self, domain_id: str) -> None:
        """Remove tags from a domain."""
        self._delete(f"/v1/domains/{domain_id}/tags")

    def list_all_tags(self) -> Dict[str, Any]:
        """Get tags assigned to all domains."""
        return self._get("/v1/domains/tags")

    # Extended domain info

    def get_capabilities(self, domain_id: str) -> Dict[str, Any]:
        """Get domain capabilities."""
        return self._get(f"/v1/domains/{domain_id}/capabilities")

    def list_all_capabilities(self) -> Dict[str, Any]:
        """Get all domain capabilities."""
        return self._get("/v1/domains/capabilities")

    def get_datacenters(self, domain_id: str) -> Dict[str, Any]:
        """Get domain datacenters."""
        return self._get(f"/v1/domains/{domain_id}/datacenters")

    def query_datastores(self, domain_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Post datastore query for a domain."""
        return self._post(f"/v1/domains/{domain_id}/datastores/queries", data=spec)

    def isolation_precheck(self, domain_id: str) -> Dict[str, Any]:
        """Perform domain isolation precheck."""
        return self._post(f"/v1/domains/{domain_id}/isolation-prechecks")

    def enable_overlay(self, domain_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Enable overlay over management network."""
        return self._patch(f"/v1/domains/{domain_id}/overlay", data=spec)

"""Host commissioning and management."""

import logging
from typing import Any, Dict, List, Optional

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import Host, Task, Validation

logger = logging.getLogger(__name__)


class HostManager(BaseManager):
    """Host commissioning and management."""

    def list(self, status: Optional[str] = None, fqdn: Optional[str] = None) -> List[Host]:
        """
        List all hosts, optionally filtered.

        Args:
            status: Filter by status (COMMISSIONED, ASSIGNED, UNASSIGNED_USEABLE, etc.)
            fqdn: Filter by FQDN (client-side, PowerVCF pattern)
        """
        endpoint = "/v1/hosts"
        if status:
            endpoint += f"?status={status}"
        response = self._get(endpoint)
        hosts = [Host(**h) for h in response.get("elements", [])]
        if fqdn:
            hosts = [h for h in hosts if h.fqdn == fqdn]
        return hosts

    def get(self, host_id: str) -> Host:
        """Get host by ID."""
        response = self._get(f"/v1/hosts/{host_id}")
        return Host(**response)

    def commission(self, hosts: List[Dict[str, Any]], validate: bool = True) -> Task:
        """
        Commission hosts into free pool.

        Args:
            hosts: List of host specs with fqdn, username, password, storageType, networkPoolId
            validate: If True, validate before commissioning (PowerVCF pattern)
        """
        if validate:
            self._validate_and_wait("/v1/hosts/validations", hosts)

        response = self._post("/v1/hosts", data=hosts)
        task_id = response.get("id")
        logger.info(f"Commissioned hosts, task ID: {task_id}")
        return Task(**self._get(f"/v1/tasks/{task_id}"))

    def decommission(self, host_id: str) -> Task:
        """Decommission a host."""
        response = self._delete(f"/v1/hosts/{host_id}")
        task_id = response.get("id")
        return Task(**self._get(f"/v1/tasks/{task_id}"))

    def validate(self, hosts: List[Dict[str, Any]]) -> Validation:
        """Validate host commissioning spec."""
        response = self._post("/v1/hosts/validations", data=hosts)
        return Validation(**response)

    def get_validation(self, validation_id: str) -> Validation:
        """Get host validation status."""
        response = self._get(f"/v1/hosts/validations/{validation_id}")
        return Validation(**response)

    # Tags

    def get_tags(self, host_id: str) -> Dict[str, Any]:
        return self._get(f"/v1/hosts/{host_id}/tags")

    def set_tags(self, host_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        return self._put(f"/v1/hosts/{host_id}/tags", data=spec)

    def delete_tags(self, host_id: str) -> None:
        self._delete(f"/v1/hosts/{host_id}/tags")

    def list_all_tags(self) -> Dict[str, Any]:
        return self._get("/v1/hosts/tags")

    # Prechecks and criteria

    def run_prechecks(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/v1/hosts/prechecks", data=spec)

    def get_precheck(self, precheck_id: str) -> Dict[str, Any]:
        return self._get(f"/v1/hosts/prechecks/{precheck_id}")

    def get_criteria(self) -> Dict[str, Any]:
        return self._get("/v1/hosts/criteria")

    def get_criterion(self, name: str) -> Dict[str, Any]:
        return self._get(f"/v1/hosts/criteria/{name}")

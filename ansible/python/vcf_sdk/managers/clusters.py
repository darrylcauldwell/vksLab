"""Cluster management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import Cluster, VDS, Task, Validation

logger = logging.getLogger(__name__)


class ClusterManager(BaseManager):
    """Cluster CRUD and validation."""

    def list(self) -> List[Cluster]:
        """List all clusters."""
        response = self._get("/v1/clusters")
        return [Cluster(**c) for c in response.get("elements", [])]

    def get(self, cluster_id: str) -> Cluster:
        """Get cluster by ID."""
        response = self._get(f"/v1/clusters/{cluster_id}")
        return Cluster(**response)

    def create(self, spec: Dict[str, Any], validate: bool = True) -> Task:
        """
        Create a cluster.

        Args:
            spec: Cluster creation spec (JSON)
            validate: If True, validate before creating
        """
        if validate:
            self._validate_and_wait(
                "/v1/clusters/validations",
                spec,
                poll_endpoint_template="/v1/clusters/validations/{id}",
            )

        response = self._post("/v1/clusters", data=spec)
        task_id = response.get("id")
        logger.info(f"Creating cluster, task ID: {task_id}")
        return Task(**self._get(f"/v1/tasks/{task_id}"))

    def update(self, cluster_id: str, spec: Dict[str, Any], validate: bool = True) -> Task:
        """
        Update (expand/compact) a cluster.

        Args:
            cluster_id: Cluster UUID
            spec: Update spec
            validate: If True, validate before updating
        """
        if validate:
            self._validate_and_wait(
                f"/v1/clusters/{cluster_id}/validations",
                spec,
            )

        response = self._patch(f"/v1/clusters/{cluster_id}", data=spec)
        task_id = response.get("id")
        logger.info(f"Updating cluster {cluster_id}, task ID: {task_id}")
        return Task(**self._get(f"/v1/tasks/{task_id}"))

    def delete(self, cluster_id: str) -> Task:
        """Delete a cluster."""
        response = self._delete(f"/v1/clusters/{cluster_id}")
        task_id = response.get("id")
        return Task(**self._get(f"/v1/tasks/{task_id}"))

    def mark_for_deletion(self, cluster_id: str) -> None:
        """Mark a cluster for deletion."""
        self._patch(f"/v1/clusters/{cluster_id}", data={"markForDeletion": True})

    def get_vdses(self, cluster_id: str) -> List[VDS]:
        """List Virtual Distributed Switches for a cluster."""
        response = self._get(f"/v1/clusters/{cluster_id}/vdses")
        return [VDS(**v) for v in response.get("elements", [])]

    def validate(self, spec: Dict[str, Any]) -> Validation:
        """Validate cluster creation spec."""
        response = self._post("/v1/clusters/validations", data=spec)
        return Validation(**response)

    def get_validation(self, validation_id: str) -> Validation:
        """Get cluster validation status."""
        response = self._get(f"/v1/clusters/validations/{validation_id}")
        return Validation(**response)

    # Tags

    def get_tags(self, cluster_id: str) -> Dict[str, Any]:
        """Get tags assigned to a cluster."""
        return self._get(f"/v1/clusters/{cluster_id}/tags")

    def set_tags(self, cluster_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Set tags on a cluster."""
        return self._put(f"/v1/clusters/{cluster_id}/tags", data=spec)

    def delete_tags(self, cluster_id: str) -> None:
        """Remove tags from a cluster."""
        self._delete(f"/v1/clusters/{cluster_id}/tags")

    def list_all_tags(self) -> Dict[str, Any]:
        """Get tags assigned to all clusters."""
        return self._get("/v1/clusters/tags")

    # Datastores

    def get_datastores(self, cluster_id: str) -> Dict[str, Any]:
        """Get datastores for a cluster."""
        return self._get(f"/v1/clusters/{cluster_id}/datastores")

    def add_datastore(self, cluster_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Add a datastore to a cluster."""
        return self._post(f"/v1/clusters/{cluster_id}/datastores", data=spec)

    def query_datastores(self, cluster_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Post datastore query for a cluster."""
        return self._post(f"/v1/clusters/{cluster_id}/datastores/queries", data=spec)

    def validate_datastore(self, cluster_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate vSanRemote datastore mount spec."""
        return self._post(f"/v1/clusters/{cluster_id}/datastores/validations", data=spec)

    def remove_datastore(self, cluster_id: str, datastore_id: str) -> Dict[str, Any]:
        """Remove a datastore from a cluster."""
        return self._delete(f"/v1/clusters/{cluster_id}/datastores/{datastore_id}")

    # Network queries

    def query_network(self, cluster_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Get cluster network configuration."""
        return self._post(f"/v1/clusters/{cluster_id}/network/queries", data=spec)

    # VDS import

    def import_vds(self, cluster_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Import VDS to cluster inventory."""
        return self._post(f"/v1/clusters/{cluster_id}/vdses", data=spec)

    # Image compliance

    def get_image_compliance(self, cluster_id: str) -> Dict[str, Any]:
        """Get cluster image compliance status."""
        return self._get(f"/v1/clusters/{cluster_id}/image-compliance")

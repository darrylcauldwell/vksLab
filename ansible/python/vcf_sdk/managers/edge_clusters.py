"""NSX Edge Cluster management (via SDDC Manager)."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import Task

logger = logging.getLogger(__name__)


class EdgeClusterManager(BaseManager):
    """NSX Edge Cluster management via SDDC Manager API."""

    def list(self) -> List[Dict[str, Any]]:
        """List all edge clusters."""
        response = self._get("/v1/edge-clusters")
        return response.get("elements", [])

    def get(self, edge_cluster_id: str) -> Dict[str, Any]:
        """Get edge cluster by ID."""
        return self._get(f"/v1/edge-clusters/{edge_cluster_id}")

    def create(self, spec: Dict[str, Any], validate: bool = True) -> Task:
        """
        Create an edge cluster.

        Args:
            spec: Edge cluster creation spec
            validate: If True, validate before creating
        """
        if validate:
            self._validate_and_wait("/v1/edge-clusters/validations", spec)

        response = self._post("/v1/edge-clusters", data=spec)
        task_id = response.get("id")
        return Task(**self._get(f"/v1/tasks/{task_id}"))

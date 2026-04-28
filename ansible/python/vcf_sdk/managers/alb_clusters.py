"""NSX ALB (Avi Load Balancer) cluster management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import Task

logger = logging.getLogger(__name__)


class ALBClusterManager(BaseManager):
    """NSX Advanced Load Balancer cluster management."""

    def list(self) -> List[Dict[str, Any]]:
        """List ALB clusters."""
        response = self._get("/v1/alb-clusters")
        return response.get("elements", [])

    def get(self, cluster_id: str) -> Dict[str, Any]:
        """Get ALB cluster by ID."""
        return self._get(f"/v1/alb-clusters/{cluster_id}")

    def deploy(self, spec: Dict[str, Any], validate: bool = True) -> Task:
        """Deploy an ALB cluster."""
        if validate:
            self._validate_and_wait("/v1/alb-clusters/validations", spec)
        response = self._post("/v1/alb-clusters", data=spec)
        task_id = response.get("id")
        return Task(**self._get(f"/v1/tasks/{task_id}"))

    def undeploy(self, cluster_id: str) -> Task:
        """Undeploy an ALB cluster."""
        response = self._delete(f"/v1/alb-clusters/{cluster_id}")
        task_id = response.get("id")
        return Task(**self._get(f"/v1/tasks/{task_id}"))

    def validate(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ALB cluster spec."""
        return self._post("/v1/alb-clusters/validations", data=spec)

    def validate_compatibility(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ALB compatibility."""
        return self._post("/v1/alb-clusters/compatibility/validations", data=spec)

    def get_form_factors(self) -> Dict[str, Any]:
        """Get ALB cluster form factors."""
        return self._get("/v1/alb-clusters/form-factors")

    def get_cluster_capacity(self) -> Dict[str, Any]:
        """Get cluster capacity for ALB deployment."""
        return self._get("/v1/alb-clusters/cluster-capacity")

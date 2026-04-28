"""VCF Management Components management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class VCFComponentManager(BaseManager):
    """VCF Management Components deployment and management."""

    def list(self) -> Dict[str, Any]:
        """Get VCF Management Components."""
        return self._get("/v1/vcf-management-components")

    def deploy(self, spec: Dict[str, Any], validate: bool = True) -> Dict[str, Any]:
        """Trigger deployment workflow."""
        if validate:
            self._validate_and_wait("/v1/vcf-management-components/validations", spec)
        return self._post("/v1/vcf-management-components", data=spec)

    def validate(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate deployment spec."""
        return self._post("/v1/vcf-management-components/validations", data=spec)

    def get_validation(self, validation_id: str) -> Dict[str, Any]:
        """Get validation results."""
        return self._get(f"/v1/vcf-management-components/validations/{validation_id}")

    def list_tasks(self) -> List[Dict[str, Any]]:
        """Get all component tasks."""
        response = self._get("/v1/vcf-management-components/tasks")
        return response.get("elements", []) if isinstance(response, dict) else response

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get component task by ID."""
        return self._get(f"/v1/vcf-management-components/tasks/{task_id}")

    def get_task_spec(self, task_id: str) -> Dict[str, Any]:
        """Get task specification."""
        return self._get(f"/v1/vcf-management-components/tasks/{task_id}/spec")

    def get_latest_task(self) -> Dict[str, Any]:
        """Get latest component task."""
        return self._get("/v1/vcf-management-components/tasks/latest")

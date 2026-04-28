"""Brownfield import management."""

import logging
from typing import Any, Dict

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class BrownfieldManager(BaseManager):
    """Import existing vCenter as VI domain (brownfield)."""

    def start_import(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Import vCenter as VI domain."""
        return self._post("/v1/sddcs/imports", data=spec)

    def get_import_task(self, task_id: str) -> Dict[str, Any]:
        """Get brownfield import task status."""
        return self._get(f"/v1/sddcs/imports/{task_id}")

    def validate_import(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate import spec."""
        return self._post("/v1/sddcs/imports/validations", data=spec)

    def get_validation_task(self, task_id: str) -> Dict[str, Any]:
        """Get import validation task status."""
        return self._get(f"/v1/sddcs/imports/validations/{task_id}")

    def synchronize(self, domain_id: str) -> Dict[str, Any]:
        """Perform synchronization for a domain."""
        return self._post(f"/v1/domains/{domain_id}/synchronizations")

    def get_sync_task(self, domain_id: str, task_id: str) -> Dict[str, Any]:
        """Get synchronization task status."""
        return self._get(f"/v1/domains/{domain_id}/synchronizations/{task_id}")

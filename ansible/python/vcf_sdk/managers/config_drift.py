"""Configuration drift reconciliation."""

import logging
from typing import Any, Dict

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class ConfigDriftManager(BaseManager):
    """Configuration drift detection and reconciliation."""

    def get_drifts(self) -> Dict[str, Any]:
        """Get configuration drifts."""
        return self._get("/v1/config-drifts")

    def reconcile(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Reconcile configuration drifts."""
        return self._post("/v1/config-drift-reconciliations", data=spec)

    def get_reconciliation_task(self, task_id: str) -> Dict[str, Any]:
        """Get reconciliation task status."""
        return self._get(f"/v1/config-drift-reconciliations/{task_id}")

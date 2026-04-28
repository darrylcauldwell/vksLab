"""Check sets management."""

import logging
from typing import Any, Dict

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class CheckSetManager(BaseManager):
    """System check sets — assessment runs and queries."""

    def get_last_run(self) -> Dict[str, Any]:
        """Get last assessment run info."""
        return self._get("/v1/system/check-sets")

    def trigger_run(self, spec: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger a check run."""
        return self._post("/v1/system/check-sets", data=spec or {})

    def query(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Query check sets for resources."""
        return self._post("/v1/system/check-sets/queries", data=spec)

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Get result of a check run."""
        return self._get(f"/v1/system/check-sets/{run_id}")

    def retry_run(self, run_id: str) -> Dict[str, Any]:
        """Trigger partial retry of a check run."""
        return self._patch(f"/v1/system/check-sets/{run_id}")

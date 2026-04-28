"""vSAN HCL and health check management."""

import logging
from typing import Any, Dict

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class VSANManager(BaseManager):
    """vSAN HCL sync and domain health checks."""

    # vSAN HCL

    def get_hcl_attributes(self) -> Dict[str, Any]:
        """Get last vSAN HCL update details."""
        return self._get("/v1/vsan-hcl/attributes")

    def get_hcl_config(self) -> Dict[str, Any]:
        """Get vSAN HCL sync settings."""
        return self._get("/v1/vsan-hcl/configuration")

    def update_hcl_config(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update vSAN HCL sync configuration."""
        return self._patch("/v1/vsan-hcl/configuration", data=spec)

    def download_hcl(self) -> Dict[str, Any]:
        """Download vSAN HCL data."""
        return self._patch("/v1/vsan-hcl")

    # vSAN Health Checks (per domain)

    def get_health_check(self, domain_id: str) -> Dict[str, Any]:
        """Get vSAN health check status for a domain."""
        return self._get(f"/v1/domains/{domain_id}/health-checks")

    def update_health_check(self, domain_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update vSAN health check status for a domain."""
        return self._patch(f"/v1/domains/{domain_id}/health-checks", data=spec)

    def get_health_check_task(self, domain_id: str, task_id: str) -> Dict[str, Any]:
        """Get vSAN health check task."""
        return self._get(f"/v1/domains/{domain_id}/health-checks/tasks/{task_id}")

    def get_health_check_query(self, domain_id: str, query_id: str) -> Dict[str, Any]:
        """Get vSAN health check query result."""
        return self._get(f"/v1/domains/{domain_id}/health-checks/queries/{query_id}")

    # UMDS sync

    def sync_umds(self, spec: Dict[str, Any] = None) -> Dict[str, Any]:
        """Sync UMDS (Update Manager Download Service)."""
        return self._patch("/v1/system/host-bundle-depot", data=spec or {})

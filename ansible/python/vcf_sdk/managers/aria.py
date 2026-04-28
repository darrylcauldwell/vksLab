"""Aria Suite (vRealize) integration management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import AriaLifecycle, AriaOperations, AriaOperationsLogs, AriaAutomation, Task

logger = logging.getLogger(__name__)


class AriaManager(BaseManager):
    """Aria Suite Lifecycle, Operations, Logs, and Automation management."""

    # Aria Suite Lifecycle Manager

    def get_lifecycle(self) -> List[AriaLifecycle]:
        """List Aria Suite Lifecycle Manager instances."""
        response = self._get("/v1/vrslcms")
        return [AriaLifecycle(**a) for a in response.get("elements", [])]

    def deploy_lifecycle(self, spec: Dict[str, Any], validate: bool = True) -> Task:
        """Deploy Aria Suite Lifecycle Manager."""
        if validate:
            self._validate_and_wait("/v1/vrslcms/validations", spec)
        response = self._post("/v1/vrslcms", data=spec)
        task_id = response.get("id")
        return Task(**self._get(f"/v1/tasks/{task_id}"))

    def remove_lifecycle(self) -> Dict[str, Any]:
        """Remove Aria Suite Lifecycle Manager."""
        return self._delete("/v1/vrslcm")

    def reset_lifecycle(self) -> Dict[str, Any]:
        """Reset Aria Suite Lifecycle Manager connection."""
        return self._patch("/v1/vrslcm")

    # Aria Operations (vROps)

    def get_operations(self) -> List[AriaOperations]:
        """List Aria Operations instances."""
        response = self._get("/v1/vropses")
        return [AriaOperations(**a) for a in response.get("elements", [])]

    def get_operations_domains(self) -> Dict[str, Any]:
        """Get domains connected to Aria Operations."""
        return self._get("/v1/vrops/domains")

    def connect_operations_domain(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Connect a domain to Aria Operations."""
        return self._put("/v1/vrops/domains", data=spec)

    # Aria Operations for Logs (vRLI)

    def get_logs(self) -> List[AriaOperationsLogs]:
        """List Aria Operations for Logs instances."""
        response = self._get("/v1/vrlis")
        return [AriaOperationsLogs(**a) for a in response.get("elements", [])]

    def get_logs_domains(self) -> Dict[str, Any]:
        """Get domains connected to Aria Operations for Logs."""
        return self._get("/v1/vrli/domains")

    def connect_logs_domain(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Connect a domain to Aria Operations for Logs."""
        return self._put("/v1/vrli/domains", data=spec)

    # Aria Automation (vRA)

    def get_automation(self) -> List[AriaAutomation]:
        """List Aria Automation instances."""
        response = self._get("/v1/vras")
        return [AriaAutomation(**a) for a in response.get("elements", [])]

    # Workspace ONE Access (WSA)

    def get_wsa(self) -> Dict[str, Any]:
        """List Workspace ONE Access instances."""
        return self._get("/v1/wsas")

"""Compliance management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import ComplianceConfiguration, ComplianceAudit

logger = logging.getLogger(__name__)


class ComplianceManager(BaseManager):
    """Compliance configuration and auditing."""

    def get_configurations(self) -> List[ComplianceConfiguration]:
        """Get compliance configurations."""
        response = self._get("/v1/compliance-configurations")
        return [ComplianceConfiguration(**c) for c in response.get("elements", [])]

    def get_standards(self) -> Dict[str, Any]:
        """Get compliance standards."""
        return self._get("/v1/compliance-standards")

    def list_audits(self, domain_id: str = None) -> List[ComplianceAudit]:
        """List compliance audits."""
        endpoint = "/v1/compliance-audits"
        if domain_id:
            endpoint = f"/v1/domains/{domain_id}/compliance-audits"
        response = self._get(endpoint)
        return [ComplianceAudit(**a) for a in response.get("elements", [])]

    def start_audit(self, spec: Dict[str, Any]) -> ComplianceAudit:
        """Start a compliance audit."""
        response = self._post("/v1/compliance-audits", data=spec)
        return ComplianceAudit(**response)

    def get_audit(self, audit_id: str) -> ComplianceAudit:
        """Get compliance audit results."""
        response = self._get(f"/v1/compliance-audits/{audit_id}")
        return ComplianceAudit(**response)

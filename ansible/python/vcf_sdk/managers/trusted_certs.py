"""Trusted certificates management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class TrustedCertificateManager(BaseManager):
    """SDDC Manager trusted certificate store."""

    def list(self) -> List[Dict[str, Any]]:
        """Get all trusted certificates."""
        response = self._get("/v1/sddc-manager/trusted-certificates")
        return response.get("elements", []) if isinstance(response, dict) else response

    def add(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Add a trusted certificate."""
        return self._post("/v1/sddc-manager/trusted-certificates", data=spec)

    def delete(self, alias: str) -> None:
        """Delete a trusted certificate by alias."""
        self._delete(f"/v1/sddc-manager/trusted-certificates/{alias}")

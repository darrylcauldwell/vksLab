"""Application Virtual Network (AVN) management."""

import logging
from typing import Any, Dict, List, Optional

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class AVNManager(BaseManager):
    """Application Virtual Network management."""

    def list(self, region_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all AVNs.

        Args:
            region_type: Optional filter — REGION_A, REGION_B, or X_REGION
        """
        endpoint = "/v1/avns"
        if region_type:
            endpoint += f"?regionType={region_type}"
        response = self._get(endpoint)
        # AVN endpoint may return list directly or wrapped
        if isinstance(response, list):
            return response
        return response.get("elements", [])

    def get(self, avn_id: str) -> Dict[str, Any]:
        """Get AVN by ID."""
        return self._get(f"/v1/avns?id={avn_id}")

    def create(self, spec: Dict[str, Any], validate: bool = True) -> Dict[str, Any]:
        """
        Create Application Virtual Networks.

        Args:
            spec: AVN creation spec (JSON)
            validate: If True, validate before creating
        """
        if validate:
            self._validate_and_wait("/v1/avns/validations", spec)

        return self._post("/v1/avns", data=spec)

    def validate(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate AVN creation spec."""
        return self._post("/v1/avns/validations", data=spec)

"""vLCM image (personality) management."""

import logging
from typing import Any, Dict, List, Optional

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import Personality

logger = logging.getLogger(__name__)


class ImageManager(BaseManager):
    """vLCM image (personality) management."""

    def list(self, name: Optional[str] = None) -> List[Personality]:
        """List all available vLCM images, optionally filtered by name."""
        endpoint = "/v1/personalities"
        if name:
            endpoint += f"?personalityName={name}"
        response = self._get(endpoint)
        return [Personality(**p) for p in response.get("elements", [])]

    def get(self, personality_id: str) -> Personality:
        """Get vLCM image by ID."""
        response = self._get(f"/v1/personalities/{personality_id}")
        return Personality(**response)

    def upload(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a new vLCM image."""
        return self._post("/v1/personalities", data=spec)

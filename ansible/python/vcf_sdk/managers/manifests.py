"""Lifecycle manifest management."""

import logging
from typing import Any, Dict

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class ManifestManager(BaseManager):
    """LCM manifest management."""

    def get(self) -> Dict[str, Any]:
        """Get latest supported LCM manifest."""
        return self._get("/v1/manifests")

    def upload(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Save/upload LCM manifest."""
        return self._post("/v1/manifests", data=spec)

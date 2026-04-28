"""Notifications management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class NotificationManager(BaseManager):
    """System notifications."""

    def list(self) -> List[Dict[str, Any]]:
        """Get all notifications."""
        response = self._get("/v1/notifications")
        return response.get("elements", []) if isinstance(response, dict) else response

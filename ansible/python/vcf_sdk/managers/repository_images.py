"""Repository image management."""

import logging
from typing import Any, Dict

from vcf_sdk.managers.base import BaseManager

logger = logging.getLogger(__name__)


class RepositoryImageManager(BaseManager):
    """Repository images for vCenter."""

    def query(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate repository images query."""
        return self._post("/v1/vcenters/repository-images/queries", data=spec)

    def get_query_result(self, query_id: str) -> Dict[str, Any]:
        """Get repository images query response."""
        return self._get(f"/v1/vcenters/repository-images/queries/{query_id}")

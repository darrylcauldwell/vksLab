"""Base manager for NSX Policy API resources.

NSX Policy API conventions:
- All paths under /policy/api/v1/infra/
- PATCH = create-or-update (idempotent)
- PUT = full replace (requires _revision)
- List responses in {"results": [...], "result_count": N}
- Resource IDs are user-defined
"""

import logging
from typing import Any, Dict, List, Type, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class NSXBaseManager:
    """Base class for NSX Policy API resource managers."""

    def __init__(self, client):
        """
        Args:
            client: NSXManager instance (has get/post/put/patch/delete methods
                    that handle auth and /policy/api/v1 prefix)
        """
        self.client = client

    def _list(self, endpoint: str, model_cls: Type[T], **params) -> List[T]:
        """List resources, handling pagination."""
        query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        url = f"{endpoint}?{query}" if query else endpoint
        response = self.client.get(url)
        return [model_cls(**item) for item in response.get("results", [])]

    def _get(self, endpoint: str, model_cls: Type[T]) -> T:
        """Get a single resource."""
        response = self.client.get(endpoint)
        return model_cls(**response)

    def _create_or_update(self, endpoint: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """PATCH — idempotent create-or-update."""
        return self.client.patch(endpoint, data=spec)

    def _replace(self, endpoint: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """PUT — full replace (requires _revision)."""
        return self.client.put(endpoint, data=spec)

    def _delete(self, endpoint: str) -> None:
        """DELETE a resource."""
        self.client.delete(endpoint)

    def _raw_get(self, endpoint: str) -> Dict[str, Any]:
        """Raw GET returning dict."""
        return self.client.get(endpoint)

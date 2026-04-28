"""Base manager for vCenter REST API resources.

vCenter REST API conventions:
- All paths under /api/
- Session auth via vmware-api-session-id header
- List endpoints return arrays directly (no wrapper)
- Some create endpoints return bare ID strings
"""

import logging
from typing import Any, Dict, List, Type, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class VCBaseManager:
    """Base class for vCenter REST API managers."""

    def __init__(self, client):
        """
        Args:
            client: VCenter instance (has get/post/put/patch/delete methods
                    that handle session auth and /api/ prefix)
        """
        self.client = client

    def _list(self, endpoint: str, model_cls: Type[T], **params) -> List[T]:
        """List resources. vCenter returns arrays directly."""
        query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        url = f"{endpoint}?{query}" if query else endpoint
        response = self.client.get(url)
        # vCenter list endpoints return arrays directly
        if isinstance(response, list):
            return [model_cls(**item) for item in response]
        # Some endpoints might still return wrapped
        if isinstance(response, dict) and "value" in response:
            return [model_cls(**item) for item in response["value"]]
        return []

    def _get(self, endpoint: str, model_cls: Type[T]) -> T:
        """Get a single resource."""
        response = self.client.get(endpoint)
        return model_cls(**response)

    def _post(self, endpoint: str, data: Dict[str, Any] = None) -> Any:
        """POST — create or action."""
        return self.client.post(endpoint, data=data)

    def _patch(self, endpoint: str, data: Dict[str, Any] = None) -> Any:
        """PATCH — partial update."""
        return self.client.patch(endpoint, data=data)

    def _put(self, endpoint: str, data: Dict[str, Any] = None) -> Any:
        """PUT — full replace."""
        return self.client.put(endpoint, data=data)

    def _delete(self, endpoint: str) -> None:
        """DELETE a resource."""
        self.client.delete(endpoint)

    def _raw_get(self, endpoint: str) -> Any:
        """Raw GET returning whatever vCenter returns."""
        return self.client.get(endpoint)

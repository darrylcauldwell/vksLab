"""Network pool management."""

import logging
from typing import Any, Dict, List, Optional

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import NetworkPool

logger = logging.getLogger(__name__)


class NetworkManager(BaseManager):
    """Network pool management."""

    def list_pools(self) -> List[NetworkPool]:
        """List all network pools."""
        response = self._get("/v1/network-pools")
        return [NetworkPool(**p) for p in response.get("elements", [])]

    def get_pool(self, pool_id: str) -> NetworkPool:
        """Get network pool by ID."""
        response = self._get(f"/v1/network-pools/{pool_id}")
        return NetworkPool(**response)

    def find_pool(self, name: str) -> Optional[NetworkPool]:
        """Find network pool by name."""
        pools = self.list_pools()
        for pool in pools:
            if pool.name == name:
                return pool
        return None

    def create_pool(self, spec: Dict[str, Any]) -> NetworkPool:
        """Create a network pool."""
        response = self._post("/v1/network-pools", data=spec)
        return NetworkPool(**response)

    def delete_pool(self, pool_id: str) -> None:
        """Delete a network pool."""
        self._delete(f"/v1/network-pools/{pool_id}")

    def list_ip_pools(self, pool_id: str) -> List[Dict[str, Any]]:
        """List IP pools within a network pool."""
        response = self._get(f"/v1/network-pools/{pool_id}/ip-pools")
        return response.get("elements", [])

    def add_ip_pool(self, pool_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Add an IP pool to a network pool."""
        return self._post(f"/v1/network-pools/{pool_id}/ip-pools", data=spec)

    def delete_ip_pool(self, pool_id: str, ip_pool_id: str) -> None:
        """Delete an IP pool from a network pool."""
        self._delete(f"/v1/network-pools/{pool_id}/ip-pools/{ip_pool_id}")

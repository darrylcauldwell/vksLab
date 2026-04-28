"""IP pool management for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx import IPPool, IPPoolSubnet, IPAllocation, IPBlock, IPBlockSubnet
from vcf_sdk.nsx.base import NSXBaseManager


class IPPoolManager(NSXBaseManager):
    """Manage IP address pools, subnets, and allocations."""

    # Pools

    def list(self) -> List[IPPool]:
        return self._list("/infra/ip-pools", IPPool)

    def get(self, pool_id: str) -> IPPool:
        return self._get(f"/infra/ip-pools/{pool_id}", IPPool)

    def create_or_update(self, pool_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", pool_id)
        return self._create_or_update(f"/infra/ip-pools/{pool_id}", spec)

    def delete(self, pool_id: str) -> None:
        self._delete(f"/infra/ip-pools/{pool_id}")

    # Subnets

    def list_subnets(self, pool_id: str) -> List[IPPoolSubnet]:
        return self._list(f"/infra/ip-pools/{pool_id}/ip-subnets", IPPoolSubnet)

    def get_subnet(self, pool_id: str, subnet_id: str) -> IPPoolSubnet:
        return self._get(f"/infra/ip-pools/{pool_id}/ip-subnets/{subnet_id}", IPPoolSubnet)

    def create_or_update_subnet(
        self, pool_id: str, subnet_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", subnet_id)
        return self._create_or_update(
            f"/infra/ip-pools/{pool_id}/ip-subnets/{subnet_id}", spec
        )

    def delete_subnet(self, pool_id: str, subnet_id: str) -> None:
        self._delete(f"/infra/ip-pools/{pool_id}/ip-subnets/{subnet_id}")

    # Allocations

    def list_allocations(self, pool_id: str) -> List[IPAllocation]:
        return self._list(f"/infra/ip-pools/{pool_id}/ip-allocations", IPAllocation)

    def get_allocation(self, pool_id: str, alloc_id: str) -> IPAllocation:
        return self._get(
            f"/infra/ip-pools/{pool_id}/ip-allocations/{alloc_id}", IPAllocation
        )

    def create_or_update_allocation(
        self, pool_id: str, alloc_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", alloc_id)
        return self._create_or_update(
            f"/infra/ip-pools/{pool_id}/ip-allocations/{alloc_id}", spec
        )

    def delete_allocation(self, pool_id: str, alloc_id: str) -> None:
        self._delete(f"/infra/ip-pools/{pool_id}/ip-allocations/{alloc_id}")

    # IP Blocks

    def list_blocks(self) -> List[IPBlock]:
        return self._list("/infra/ip-blocks", IPBlock)

    def get_block(self, block_id: str) -> IPBlock:
        return self._get(f"/infra/ip-blocks/{block_id}", IPBlock)

    def create_or_update_block(self, block_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", block_id)
        return self._create_or_update(f"/infra/ip-blocks/{block_id}", spec)

    def delete_block(self, block_id: str) -> None:
        self._delete(f"/infra/ip-blocks/{block_id}")

    # IP Block Subnets

    def list_block_subnets(self, block_id: str) -> List[IPBlockSubnet]:
        return self._list(f"/infra/ip-blocks/{block_id}/ip-subnets", IPBlockSubnet)

    def get_block_subnet(self, block_id: str, subnet_id: str) -> IPBlockSubnet:
        return self._get(f"/infra/ip-blocks/{block_id}/ip-subnets/{subnet_id}", IPBlockSubnet)

    def create_or_update_block_subnet(
        self, block_id: str, subnet_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", subnet_id)
        return self._create_or_update(
            f"/infra/ip-blocks/{block_id}/ip-subnets/{subnet_id}", spec
        )

    def delete_block_subnet(self, block_id: str, subnet_id: str) -> None:
        self._delete(f"/infra/ip-blocks/{block_id}/ip-subnets/{subnet_id}")

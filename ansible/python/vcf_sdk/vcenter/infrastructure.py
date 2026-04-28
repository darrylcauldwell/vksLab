"""Infrastructure management (clusters, datacenters, datastores, hosts, networks) for vCenter REST API."""

from typing import Any, Dict, List

from vcf_sdk.models.vcenter import (
    Cluster, Datacenter, Datastore, HostSummary, Network, ResourcePool, StoragePolicy,
)
from vcf_sdk.vcenter.base import VCBaseManager


class InfrastructureManager(VCBaseManager):
    """Read infrastructure: clusters, datacenters, datastores, hosts, networks, resource pools, storage policies."""

    # Clusters

    def list_clusters(self, **filters) -> List[Cluster]:
        params = {f"filter.{k}": v for k, v in filters.items() if v is not None}
        return self._list("/vcenter/cluster", Cluster, **params)

    def get_cluster(self, cluster_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/cluster/{cluster_id}")

    # Datacenters

    def list_datacenters(self, **filters) -> List[Datacenter]:
        params = {f"filter.{k}": v for k, v in filters.items() if v is not None}
        return self._list("/vcenter/datacenter", Datacenter, **params)

    def get_datacenter(self, dc_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/datacenter/{dc_id}")

    def create_datacenter(self, spec: Dict[str, Any]) -> str:
        """Create a datacenter. Returns datacenter identifier."""
        return self._post("/vcenter/datacenter", data=spec)

    def delete_datacenter(self, dc_id: str) -> None:
        self._delete(f"/vcenter/datacenter/{dc_id}")

    # Datastores

    def list_datastores(self, **filters) -> List[Datastore]:
        params = {f"filter.{k}": v for k, v in filters.items() if v is not None}
        return self._list("/vcenter/datastore", Datastore, **params)

    def get_datastore(self, ds_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/datastore/{ds_id}")

    # Hosts

    def list_hosts(self, **filters) -> List[HostSummary]:
        params = {f"filter.{k}": v for k, v in filters.items() if v is not None}
        return self._list("/vcenter/host", HostSummary, **params)

    def get_host(self, host_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/host/{host_id}")

    # Networks

    def list_networks(self, **filters) -> List[Network]:
        params = {f"filter.{k}": v for k, v in filters.items() if v is not None}
        return self._list("/vcenter/network", Network, **params)

    # Resource Pools

    def list_resource_pools(self, **filters) -> List[ResourcePool]:
        params = {f"filter.{k}": v for k, v in filters.items() if v is not None}
        return self._list("/vcenter/resource-pool", ResourcePool, **params)

    def get_resource_pool(self, rp_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/resource-pool/{rp_id}")

    def create_resource_pool(self, spec: Dict[str, Any]) -> str:
        """Create a resource pool. Returns resource pool identifier."""
        return self._post("/vcenter/resource-pool", data=spec)

    def update_resource_pool(self, rp_id: str, spec: Dict[str, Any]) -> None:
        self._patch(f"/vcenter/resource-pool/{rp_id}", data=spec)

    def delete_resource_pool(self, rp_id: str) -> None:
        self._delete(f"/vcenter/resource-pool/{rp_id}")

    # Storage Policies

    def list_storage_policies(self) -> List[StoragePolicy]:
        return self._list("/vcenter/storage/policies", StoragePolicy)

    def get_storage_policy(self, policy_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/vcenter/storage/policies/{policy_id}")

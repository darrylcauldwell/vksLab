"""Namespace management (Tanzu/VKS) for vCenter REST API."""

from typing import Any, Dict, List

from vcf_sdk.models.vcenter import SupervisorCluster, Namespace, NamespaceAccess
from vcf_sdk.vcenter.base import VCBaseManager


class NamespaceManager(VCBaseManager):
    """Manage Supervisor clusters, namespaces, and access control."""

    # Supervisor Clusters

    def list_supervisors(self) -> List[SupervisorCluster]:
        """List Supervisor-enabled clusters."""
        return self._list("/vcenter/namespace-management/clusters", SupervisorCluster)

    def get_supervisor(self, cluster_id: str) -> SupervisorCluster:
        """Get Supervisor cluster info."""
        return self._get(
            f"/vcenter/namespace-management/clusters/{cluster_id}", SupervisorCluster
        )

    def enable_supervisor(self, cluster_id: str, spec: Dict[str, Any]) -> None:
        """Enable Supervisor on a cluster."""
        self._post(
            f"/vcenter/namespace-management/clusters/{cluster_id}?action=enable",
            data=spec,
        )

    def disable_supervisor(self, cluster_id: str) -> None:
        """Disable Supervisor on a cluster."""
        self._post(
            f"/vcenter/namespace-management/clusters/{cluster_id}?action=disable"
        )

    def update_supervisor(self, cluster_id: str, spec: Dict[str, Any]) -> None:
        """Update Supervisor cluster configuration."""
        self._put(f"/vcenter/namespace-management/clusters/{cluster_id}", data=spec)

    # Namespaces

    def list_namespaces(self) -> List[Namespace]:
        """List all namespaces."""
        return self._list("/vcenter/namespaces/instances", Namespace)

    def get_namespace(self, namespace: str) -> Namespace:
        """Get namespace details."""
        return self._get(f"/vcenter/namespaces/instances/{namespace}", Namespace)

    def create_namespace(self, spec: Dict[str, Any]) -> None:
        """Create a namespace."""
        self._post("/vcenter/namespaces/instances", data=spec)

    def update_namespace(self, namespace: str, spec: Dict[str, Any]) -> None:
        """Update a namespace."""
        self._patch(f"/vcenter/namespaces/instances/{namespace}", data=spec)

    def delete_namespace(self, namespace: str) -> None:
        """Delete a namespace."""
        self._delete(f"/vcenter/namespaces/instances/{namespace}")

    # Namespace Access

    def list_access(self, namespace: str) -> List[NamespaceAccess]:
        """List access entries for a namespace."""
        return self._list(
            f"/vcenter/namespaces/instances/{namespace}/access", NamespaceAccess
        )

    def set_access(
        self, namespace: str, domain: str, subject: str, spec: Dict[str, Any]
    ) -> None:
        """Set access/permissions on a namespace."""
        self._put(
            f"/vcenter/namespaces/instances/{namespace}/access/{domain}/{subject}",
            data=spec,
        )

    def remove_access(self, namespace: str, domain: str, subject: str) -> None:
        """Remove access from a namespace."""
        self._delete(
            f"/vcenter/namespaces/instances/{namespace}/access/{domain}/{subject}"
        )

"""Fabric management (transport zones, edge clusters, transport nodes, profiles, sites) for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx import (
    TransportZone, EdgeCluster, EdgeNode,
    Site, EnforcementPoint, HostTransportNode, TransportNodeCollection,
    TransportNodeProfile, EdgeTransportNode, HostSwitchProfile, EdgeHAProfile,
    ComputeSubCluster,
)
from vcf_sdk.nsx.base import NSXBaseManager

SITE_PATH = "/infra/sites/default/enforcement-points/default"


class TransportZoneManager(NSXBaseManager):
    """List transport zones (read-only from Policy API)."""

    def list(self) -> List[TransportZone]:
        return self._list(f"{SITE_PATH}/transport-zones", TransportZone)

    def get(self, tz_id: str) -> TransportZone:
        return self._get(f"{SITE_PATH}/transport-zones/{tz_id}", TransportZone)


class EdgeClusterManager(NSXBaseManager):
    """List edge clusters and nodes (read-only from Policy API)."""

    def list(self) -> List[EdgeCluster]:
        return self._list(f"{SITE_PATH}/edge-clusters", EdgeCluster)

    def get(self, ec_id: str) -> EdgeCluster:
        return self._get(f"{SITE_PATH}/edge-clusters/{ec_id}", EdgeCluster)

    def list_nodes(self, ec_id: str) -> List[EdgeNode]:
        return self._list(f"{SITE_PATH}/edge-clusters/{ec_id}/edge-nodes", EdgeNode)

    def get_node(self, ec_id: str, node_id: str) -> EdgeNode:
        return self._get(
            f"{SITE_PATH}/edge-clusters/{ec_id}/edge-nodes/{node_id}", EdgeNode
        )


class HostTransportNodeManager(NSXBaseManager):
    """Manage host transport nodes."""

    def list(self, site: str = "default", ep: str = "default") -> List[HostTransportNode]:
        return self._list(
            f"/infra/sites/{site}/enforcement-points/{ep}/host-transport-nodes",
            HostTransportNode,
        )

    def get(self, node_id: str, site: str = "default", ep: str = "default") -> HostTransportNode:
        return self._get(
            f"/infra/sites/{site}/enforcement-points/{ep}/host-transport-nodes/{node_id}",
            HostTransportNode,
        )

    def create_or_update(
        self, node_id: str, spec: Dict[str, Any], site: str = "default", ep: str = "default"
    ) -> Dict[str, Any]:
        spec.setdefault("id", node_id)
        return self._create_or_update(
            f"/infra/sites/{site}/enforcement-points/{ep}/host-transport-nodes/{node_id}", spec
        )

    def delete(self, node_id: str, site: str = "default", ep: str = "default") -> None:
        self._delete(
            f"/infra/sites/{site}/enforcement-points/{ep}/host-transport-nodes/{node_id}"
        )

    def restore_cluster_config(
        self, node_id: str, site: str = "default", ep: str = "default"
    ) -> Dict[str, Any]:
        return self._raw_get(
            f"/infra/sites/{site}/enforcement-points/{ep}/host-transport-nodes/{node_id}"
            "?action=restore_cluster_config"
        )


class TransportNodeCollectionManager(NSXBaseManager):
    """Manage transport node collections (cluster-level auto-TN config)."""

    def list(self, site: str = "default", ep: str = "default") -> List[TransportNodeCollection]:
        return self._list(
            f"/infra/sites/{site}/enforcement-points/{ep}/transport-node-collections",
            TransportNodeCollection,
        )

    def get(
        self, collection_id: str, site: str = "default", ep: str = "default"
    ) -> TransportNodeCollection:
        return self._get(
            f"/infra/sites/{site}/enforcement-points/{ep}/transport-node-collections/{collection_id}",
            TransportNodeCollection,
        )

    def create_or_update(
        self, collection_id: str, spec: Dict[str, Any],
        site: str = "default", ep: str = "default"
    ) -> Dict[str, Any]:
        spec.setdefault("id", collection_id)
        return self._create_or_update(
            f"/infra/sites/{site}/enforcement-points/{ep}/transport-node-collections/{collection_id}",
            spec,
        )

    def delete(
        self, collection_id: str, site: str = "default", ep: str = "default"
    ) -> None:
        self._delete(
            f"/infra/sites/{site}/enforcement-points/{ep}/transport-node-collections/{collection_id}"
        )


class TransportNodeProfileManager(NSXBaseManager):
    """Manage host transport node profiles."""

    def list(self) -> List[TransportNodeProfile]:
        return self._list("/infra/host-transport-node-profiles", TransportNodeProfile)

    def get(self, profile_id: str) -> TransportNodeProfile:
        return self._get(f"/infra/host-transport-node-profiles/{profile_id}", TransportNodeProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/host-transport-node-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/host-transport-node-profiles/{profile_id}")


class EdgeTransportNodeManager(NSXBaseManager):
    """Manage edge transport nodes."""

    def list(self, site: str = "default", ep: str = "default") -> List[EdgeTransportNode]:
        return self._list(
            f"/infra/sites/{site}/enforcement-points/{ep}/edge-transport-nodes",
            EdgeTransportNode,
        )

    def get(self, node_id: str, site: str = "default", ep: str = "default") -> EdgeTransportNode:
        return self._get(
            f"/infra/sites/{site}/enforcement-points/{ep}/edge-transport-nodes/{node_id}",
            EdgeTransportNode,
        )

    def create_or_update(
        self, node_id: str, spec: Dict[str, Any], site: str = "default", ep: str = "default"
    ) -> Dict[str, Any]:
        spec.setdefault("id", node_id)
        return self._create_or_update(
            f"/infra/sites/{site}/enforcement-points/{ep}/edge-transport-nodes/{node_id}", spec
        )

    def delete(self, node_id: str, site: str = "default", ep: str = "default") -> None:
        self._delete(
            f"/infra/sites/{site}/enforcement-points/{ep}/edge-transport-nodes/{node_id}"
        )


class HostSwitchProfileManager(NSXBaseManager):
    """Manage host switch profiles (uplink, VTEP HA)."""

    def list(self) -> List[HostSwitchProfile]:
        return self._list("/infra/host-switch-profiles", HostSwitchProfile)

    def get(self, profile_id: str) -> HostSwitchProfile:
        return self._get(f"/infra/host-switch-profiles/{profile_id}", HostSwitchProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/host-switch-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/host-switch-profiles/{profile_id}")


class EdgeHAProfileManager(NSXBaseManager):
    """Manage edge high availability profiles."""

    def list(self) -> List[EdgeHAProfile]:
        return self._list("/infra/edge-high-availability-profiles", EdgeHAProfile)

    def get(self, profile_id: str) -> EdgeHAProfile:
        return self._get(f"/infra/edge-high-availability-profiles/{profile_id}", EdgeHAProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(
            f"/infra/edge-high-availability-profiles/{profile_id}", spec
        )

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/edge-high-availability-profiles/{profile_id}")


class SiteManager(NSXBaseManager):
    """Manage NSX sites and enforcement points."""

    def list_sites(self) -> List[Site]:
        return self._list("/infra/sites", Site)

    def get_site(self, site_id: str) -> Site:
        return self._get(f"/infra/sites/{site_id}", Site)

    def create_or_update_site(self, site_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", site_id)
        return self._create_or_update(f"/infra/sites/{site_id}", spec)

    def delete_site(self, site_id: str) -> None:
        self._delete(f"/infra/sites/{site_id}")

    def list_enforcement_points(self, site_id: str) -> List[EnforcementPoint]:
        return self._list(f"/infra/sites/{site_id}/enforcement-points", EnforcementPoint)

    def get_enforcement_point(self, site_id: str, ep_id: str) -> EnforcementPoint:
        return self._get(f"/infra/sites/{site_id}/enforcement-points/{ep_id}", EnforcementPoint)

    def create_or_update_enforcement_point(
        self, site_id: str, ep_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", ep_id)
        return self._create_or_update(
            f"/infra/sites/{site_id}/enforcement-points/{ep_id}", spec
        )


class ComputeSubClusterManager(NSXBaseManager):
    """Manage compute sub-clusters."""

    def list(self, site: str = "default", ep: str = "default") -> List[ComputeSubCluster]:
        return self._list(
            f"/infra/sites/{site}/enforcement-points/{ep}/compute-sub-clusters",
            ComputeSubCluster,
        )

    def get(
        self, sub_cluster_id: str, site: str = "default", ep: str = "default"
    ) -> ComputeSubCluster:
        return self._get(
            f"/infra/sites/{site}/enforcement-points/{ep}/compute-sub-clusters/{sub_cluster_id}",
            ComputeSubCluster,
        )

    def create_or_update(
        self, sub_cluster_id: str, spec: Dict[str, Any],
        site: str = "default", ep: str = "default"
    ) -> Dict[str, Any]:
        spec.setdefault("id", sub_cluster_id)
        return self._create_or_update(
            f"/infra/sites/{site}/enforcement-points/{ep}/compute-sub-clusters/{sub_cluster_id}",
            spec,
        )

    def delete(
        self, sub_cluster_id: str, site: str = "default", ep: str = "default"
    ) -> None:
        self._delete(
            f"/infra/sites/{site}/enforcement-points/{ep}/compute-sub-clusters/{sub_cluster_id}"
        )

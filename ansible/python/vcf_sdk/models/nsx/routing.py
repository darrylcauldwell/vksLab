"""Routing models (OSPF, prefix lists, route maps, redistribution) for NSX-T Policy API."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class OSPFConfig(NSXResource):
    """OSPF configuration on a Tier-0 locale service."""

    enabled: Optional[bool] = Field(default=None)
    ecmp: Optional[bool] = Field(default=None)
    graceful_restart_config: Optional[Dict[str, Any]] = Field(default=None)
    default_originate: Optional[bool] = Field(default=None)


class OSPFArea(NSXResource):
    """OSPF area configuration."""

    area_id: Optional[str] = Field(default=None)
    area_type: Optional[str] = Field(default=None, description="NORMAL, NSSA, STUB")
    auth_mode: Optional[str] = Field(default=None)


class PrefixList(NSXResource):
    """Gateway prefix list for route filtering."""

    prefixes: Optional[List[Dict[str, Any]]] = Field(default=None)


class CommunityList(NSXResource):
    """BGP community list."""

    communities: Optional[List[str]] = Field(default=None)


class RouteMap(NSXResource):
    """Gateway route map."""

    entries: Optional[List[Dict[str, Any]]] = Field(default=None)


class SegmentPort(NSXResource):
    """Segment port."""

    attachment: Optional[Dict[str, Any]] = Field(default=None)
    address_bindings: Optional[List[Dict[str, Any]]] = Field(default=None)


class IPBlock(NSXResource):
    """IP address block."""

    cidr: Optional[str] = Field(default=None)


class IPBlockSubnet(NSXResource):
    """Subnet within an IP block."""

    cidr: Optional[str] = Field(default=None)
    allocation_size: Optional[int] = Field(default=None)


class Site(NSXResource):
    """NSX site (for multi-site / federation)."""

    site_type: Optional[str] = Field(default=None)


class EnforcementPoint(NSXResource):
    """Enforcement point within a site."""

    connection_info: Optional[List[Dict[str, Any]]] = Field(default=None)
    resource_type: Optional[str] = Field(default=None)


class HostTransportNode(NSXResource):
    """Host transport node."""

    node_deployment_info: Optional[Dict[str, Any]] = Field(default=None)
    host_switch_spec: Optional[Dict[str, Any]] = Field(default=None)
    maintenance_mode: Optional[str] = Field(default=None)


class TransportNodeCollection(NSXResource):
    """Transport node collection (cluster-level auto-TN config)."""

    compute_collection_id: Optional[str] = Field(default=None)
    transport_node_profile_id: Optional[str] = Field(default=None)


class TransportNodeProfile(NSXResource):
    """Host transport node profile."""

    host_switch_spec: Optional[Dict[str, Any]] = Field(default=None)


class EdgeTransportNode(NSXResource):
    """Edge transport node."""

    node_deployment_info: Optional[Dict[str, Any]] = Field(default=None)
    host_switch_spec: Optional[Dict[str, Any]] = Field(default=None)
    remote_tunnel_endpoint: Optional[Dict[str, Any]] = Field(default=None)


class HostSwitchProfile(NSXResource):
    """Host switch profile (uplink or VTEP HA)."""

    teaming: Optional[Dict[str, Any]] = Field(default=None)
    transport_vlan: Optional[int] = Field(default=None)
    lags: Optional[List[Dict[str, Any]]] = Field(default=None)


class EdgeHAProfile(NSXResource):
    """Edge high availability profile."""

    bfd_probe_interval: Optional[int] = Field(default=None)
    bfd_allowed_hops: Optional[int] = Field(default=None)
    standby_relocation_config: Optional[Dict[str, Any]] = Field(default=None)


class ComputeSubCluster(NSXResource):
    """Compute sub-cluster."""

    compute_collection_id: Optional[str] = Field(default=None)

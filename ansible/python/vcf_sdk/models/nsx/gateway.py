"""Gateway models for NSX-T Policy API."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class Tier0Gateway(NSXResource):
    """NSX-T Tier-0 gateway."""

    ha_mode: Optional[str] = Field(default=None, description="ACTIVE_ACTIVE or ACTIVE_STANDBY")
    failover_mode: Optional[str] = Field(default=None, description="PREEMPTIVE or NON_PREEMPTIVE")
    transit_subnets: Optional[List[str]] = Field(default=None)
    internal_transit_subnets: Optional[List[str]] = Field(default=None)


class Tier1Gateway(NSXResource):
    """NSX-T Tier-1 gateway."""

    tier0_path: Optional[str] = Field(default=None, description="Path to parent Tier-0")
    failover_mode: Optional[str] = Field(default=None)
    route_advertisement_types: Optional[List[str]] = Field(default=None)
    dhcp_config_paths: Optional[List[str]] = Field(default=None)


class LocaleService(NSXResource):
    """Gateway locale service (binds gateway to edge cluster)."""

    edge_cluster_path: Optional[str] = Field(default=None)
    preferred_edge_paths: Optional[List[str]] = Field(default=None)


class GatewayInterface(NSXResource):
    """Gateway interface (uplink or service interface)."""

    type: Optional[str] = Field(default=None, description="EXTERNAL, SERVICE, etc.")
    segment_path: Optional[str] = Field(default=None)
    subnets: Optional[List[Dict[str, Any]]] = Field(default=None)
    edge_node_path: Optional[str] = Field(default=None)
    mtu: Optional[int] = Field(default=None)


class StaticRoute(NSXResource):
    """Static route on a gateway."""

    network: Optional[str] = Field(default=None, description="Destination CIDR")
    next_hops: Optional[List[Dict[str, Any]]] = Field(default=None)


class BGPConfig(NSXResource):
    """BGP configuration for a Tier-0 locale service."""

    local_as_num: Optional[str] = Field(default=None)
    enabled: Optional[bool] = Field(default=None)
    inter_sr_ibgp: Optional[bool] = Field(default=None)
    ecmp: Optional[bool] = Field(default=None)
    multipath_relax: Optional[bool] = Field(default=None)
    graceful_restart_config: Optional[Dict[str, Any]] = Field(default=None)
    route_aggregations: Optional[List[Dict[str, Any]]] = Field(default=None)


class BGPNeighbor(NSXResource):
    """BGP neighbor configuration."""

    neighbor_address: Optional[str] = Field(default=None)
    remote_as_num: Optional[str] = Field(default=None)
    hold_down_time: Optional[int] = Field(default=None)
    keep_alive_time: Optional[int] = Field(default=None)
    source_addresses: Optional[List[str]] = Field(default=None)
    allow_as_in: Optional[bool] = Field(default=None)
    bfd: Optional[Dict[str, Any]] = Field(default=None)

"""Infrastructure profiles for NSX-T Policy API."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class IPDiscoveryProfile(NSXResource):
    """IP discovery profile for segments."""

    arp_nd_binding_timeout: Optional[int] = Field(default=None)
    duplicate_ip_detection: Optional[Dict[str, Any]] = Field(default=None)
    arp_snooping_config: Optional[Dict[str, Any]] = Field(default=None)
    dhcp_snooping_config: Optional[Dict[str, Any]] = Field(default=None)
    vmtools_config: Optional[Dict[str, Any]] = Field(default=None)
    nd_snooping_config: Optional[Dict[str, Any]] = Field(default=None)


class MACDiscoveryProfile(NSXResource):
    """MAC discovery profile for segments."""

    mac_change_enabled: Optional[bool] = Field(default=None)
    mac_learning_enabled: Optional[bool] = Field(default=None)
    mac_limit: Optional[int] = Field(default=None)
    mac_limit_policy: Optional[str] = Field(default=None, description="ALLOW or DROP")
    unknown_unicast_flooding_enabled: Optional[bool] = Field(default=None)


class SpoofGuardProfile(NSXResource):
    """Spoof guard profile for segments."""

    address_binding_allowlist: Optional[bool] = Field(default=None)
    address_binding_whitelist: Optional[bool] = Field(default=None)


class SegmentSecurityProfile(NSXResource):
    """Segment security profile."""

    bpdu_filter: Optional[Dict[str, Any]] = Field(default=None)
    dhcp_client_block_enabled: Optional[bool] = Field(default=None)
    dhcp_client_block_v6_enabled: Optional[bool] = Field(default=None)
    dhcp_server_block_enabled: Optional[bool] = Field(default=None)
    dhcp_server_block_v6_enabled: Optional[bool] = Field(default=None)
    non_ip_traffic_block_enabled: Optional[bool] = Field(default=None)
    ra_guard_enabled: Optional[bool] = Field(default=None)
    rate_limits: Optional[Dict[str, Any]] = Field(default=None)


class QoSProfile(NSXResource):
    """QoS profile for gateways."""

    dscp: Optional[Dict[str, Any]] = Field(default=None)
    shaper_configurations: Optional[List[Dict[str, Any]]] = Field(default=None)
    class_of_service: Optional[int] = Field(default=None)


class GatewayQoSProfile(NSXResource):
    """Gateway-level QoS profile."""

    committed_bandwidths: Optional[List[Dict[str, Any]]] = Field(default=None)
    burst_size: Optional[int] = Field(default=None)
    excess_action: Optional[str] = Field(default=None)


class FloodProtectionProfile(NSXResource):
    """Flood protection profile (gateway or distributed)."""

    udp_active_flow_limit: Optional[int] = Field(default=None)
    icmp_active_flow_limit: Optional[int] = Field(default=None)
    tcp_half_open_conn_limit: Optional[int] = Field(default=None)
    other_active_conn_limit: Optional[int] = Field(default=None)
    rst_spoofing_enabled: Optional[bool] = Field(default=None)
    nat_active_conn_limit: Optional[int] = Field(default=None)
    enable_syncache: Optional[bool] = Field(default=None)


class FloodProtectionProfileBinding(NSXResource):
    """Binding of a flood protection profile to a gateway or segment."""

    profile_path: Optional[str] = Field(default=None)

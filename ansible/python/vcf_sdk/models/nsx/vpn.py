"""VPN models for NSX-T Policy API."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class IPSecVPNService(NSXResource):
    """IPSec VPN service on a Tier-0 or Tier-1 gateway."""

    enabled: Optional[bool] = Field(default=None)
    ike_log_level: Optional[str] = Field(default=None, description="DEBUG, INFO, WARN, ERROR")


class IPSecVPNSession(NSXResource):
    """IPSec VPN session (route-based or policy-based)."""

    resource_type: Optional[str] = Field(
        default=None, description="RouteBasedIPSecVpnSession or PolicyBasedIPSecVpnSession"
    )
    enabled: Optional[bool] = Field(default=None)
    local_endpoint_path: Optional[str] = Field(default=None)
    peer_address: Optional[str] = Field(default=None)
    peer_id: Optional[str] = Field(default=None)
    authentication_mode: Optional[str] = Field(default=None, description="PSK or CERTIFICATE")
    psk: Optional[str] = Field(default=None, description="Pre-shared key")
    ike_profile_path: Optional[str] = Field(default=None)
    tunnel_profile_path: Optional[str] = Field(default=None)
    dpd_profile_path: Optional[str] = Field(default=None)
    compliance_suite: Optional[str] = Field(default=None)
    # Route-based
    tunnel_interfaces: Optional[List[Dict[str, Any]]] = Field(default=None)
    # Policy-based
    rules: Optional[List[Dict[str, Any]]] = Field(default=None)


class IPSecVPNLocalEndpoint(NSXResource):
    """IPSec VPN local endpoint."""

    local_address: Optional[str] = Field(default=None)
    local_id: Optional[str] = Field(default=None)
    certificate_path: Optional[str] = Field(default=None)
    trust_ca_paths: Optional[List[str]] = Field(default=None)
    trust_crl_paths: Optional[List[str]] = Field(default=None)


class IPSecVPNIKEProfile(NSXResource):
    """IKE profile for IPSec VPN."""

    ike_version: Optional[str] = Field(default=None, description="IKE_V1 or IKE_V2")
    encryption_algorithms: Optional[List[str]] = Field(default=None)
    digest_algorithms: Optional[List[str]] = Field(default=None)
    dh_groups: Optional[List[str]] = Field(default=None)
    sa_life_time: Optional[int] = Field(default=None)


class IPSecVPNTunnelProfile(NSXResource):
    """Tunnel profile for IPSec VPN."""

    encryption_algorithms: Optional[List[str]] = Field(default=None)
    digest_algorithms: Optional[List[str]] = Field(default=None)
    dh_groups: Optional[List[str]] = Field(default=None)
    sa_life_time: Optional[int] = Field(default=None)
    enable_perfect_forward_secrecy: Optional[bool] = Field(default=None)
    df_policy: Optional[str] = Field(default=None, description="COPY, CLEAR")


class IPSecVPNDPDProfile(NSXResource):
    """Dead Peer Detection profile for IPSec VPN."""

    dpd_probe_mode: Optional[str] = Field(default=None, description="PERIODIC or ON_DEMAND")
    dpd_probe_interval: Optional[int] = Field(default=None)
    enabled: Optional[bool] = Field(default=None)
    retry_count: Optional[int] = Field(default=None)


class L2VPNService(NSXResource):
    """L2 VPN service."""

    enabled: Optional[bool] = Field(default=None)
    mode: Optional[str] = Field(default=None, description="SERVER or CLIENT")


class L2VPNSession(NSXResource):
    """L2 VPN session."""

    transport_tunnels: Optional[List[str]] = Field(default=None)
    enabled: Optional[bool] = Field(default=None)

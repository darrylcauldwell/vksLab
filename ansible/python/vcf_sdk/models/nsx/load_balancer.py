"""Load Balancer models for NSX-T Policy API."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class LBService(NSXResource):
    """Load Balancer service attached to a Tier-1 gateway."""

    enabled: Optional[bool] = Field(default=None)
    size: Optional[str] = Field(default=None, description="SMALL, MEDIUM, LARGE, XLARGE, DLB")
    connectivity_path: Optional[str] = Field(default=None, description="Tier-1 gateway path")
    error_log_level: Optional[str] = Field(default=None)
    access_log_enabled: Optional[bool] = Field(default=None)


class LBVirtualServer(NSXResource):
    """Load Balancer virtual server."""

    enabled: Optional[bool] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    ports: Optional[List[str]] = Field(default=None)
    lb_service_path: Optional[str] = Field(default=None)
    pool_path: Optional[str] = Field(default=None)
    application_profile_path: Optional[str] = Field(default=None)
    lb_persistence_profile_path: Optional[str] = Field(default=None)
    client_ssl_profile_binding: Optional[Dict[str, Any]] = Field(default=None)
    server_ssl_profile_binding: Optional[Dict[str, Any]] = Field(default=None)
    default_pool_member_ports: Optional[List[str]] = Field(default=None)
    sorry_pool_path: Optional[str] = Field(default=None)
    max_concurrent_connections: Optional[int] = Field(default=None)
    max_new_connection_rate: Optional[int] = Field(default=None)
    rules: Optional[List[Dict[str, Any]]] = Field(default=None)
    access_log_enabled: Optional[bool] = Field(default=None)
    log_significant_event_only: Optional[bool] = Field(default=None)


class LBPool(NSXResource):
    """Load Balancer server pool."""

    algorithm: Optional[str] = Field(
        default=None, description="ROUND_ROBIN, WEIGHTED_ROUND_ROBIN, LEAST_CONNECTION, etc."
    )
    members: Optional[List[Dict[str, Any]]] = Field(default=None)
    member_group: Optional[Dict[str, Any]] = Field(default=None)
    snat_translation: Optional[Dict[str, Any]] = Field(default=None)
    active_monitor_paths: Optional[List[str]] = Field(default=None)
    passive_monitor_path: Optional[str] = Field(default=None)
    tcp_multiplexing_enabled: Optional[bool] = Field(default=None)
    tcp_multiplexing_number: Optional[int] = Field(default=None)
    min_active_members: Optional[int] = Field(default=None)


class LBMonitorProfile(NSXResource):
    """Load Balancer monitor profile (HTTP, HTTPS, TCP, UDP, ICMP, passive)."""

    monitor_port: Optional[int] = Field(default=None)
    fall_count: Optional[int] = Field(default=None)
    rise_count: Optional[int] = Field(default=None)
    interval: Optional[int] = Field(default=None)
    timeout: Optional[int] = Field(default=None)
    # HTTP/HTTPS specific
    request_method: Optional[str] = Field(default=None)
    request_url: Optional[str] = Field(default=None)
    request_body: Optional[str] = Field(default=None)
    request_headers: Optional[List[Dict[str, str]]] = Field(default=None)
    response_status_codes: Optional[List[int]] = Field(default=None)
    response_body: Optional[str] = Field(default=None)
    # SSL
    server_ssl_profile_binding: Optional[Dict[str, Any]] = Field(default=None)


class LBAppProfile(NSXResource):
    """Load Balancer application profile (HTTP, fast TCP, fast UDP)."""

    # HTTP specific
    idle_timeout: Optional[int] = Field(default=None)
    request_header_size: Optional[int] = Field(default=None)
    response_header_size: Optional[int] = Field(default=None)
    http_redirect_to_https: Optional[bool] = Field(default=None)
    x_forwarded_for: Optional[str] = Field(default=None)
    ntlm: Optional[bool] = Field(default=None)
    # TCP/UDP specific
    close_timeout: Optional[int] = Field(default=None)
    ha_flow_mirroring_enabled: Optional[bool] = Field(default=None)


class LBPersistenceProfile(NSXResource):
    """Load Balancer persistence profile (cookie, source IP, generic)."""

    persistence_shared: Optional[bool] = Field(default=None)
    ha_persistence_mirroring_enabled: Optional[bool] = Field(default=None)
    purge: Optional[str] = Field(default=None)
    timeout: Optional[int] = Field(default=None)
    # Cookie specific
    cookie_name: Optional[str] = Field(default=None)
    cookie_mode: Optional[str] = Field(default=None)
    cookie_garble: Optional[bool] = Field(default=None)
    cookie_fallback: Optional[bool] = Field(default=None)


class LBSSLProfile(NSXResource):
    """Load Balancer SSL profile (client or server)."""

    protocols: Optional[List[str]] = Field(default=None)
    ciphers: Optional[List[str]] = Field(default=None)
    cipher_group_path: Optional[str] = Field(default=None)
    session_cache_enabled: Optional[bool] = Field(default=None)
    prefer_server_ciphers: Optional[bool] = Field(default=None)

"""NSX Manager API client (Policy API)."""

import logging
import re
from typing import Any, Dict, Optional

from vcf_sdk.base import BaseClient
from vcf_sdk.nsx import (
    SegmentManager, Tier0Manager, Tier1Manager,
    GroupManager, SecurityPolicyManager, GatewayPolicyManager,
    ServiceManager, NATManager, DHCPManager, DNSManager,
    IPPoolManager, NSXEdgeClusterManager, TransportZoneManager,
    HostTransportNodeManager, TransportNodeCollectionManager,
    TransportNodeProfileManager, EdgeTransportNodeManager,
    HostSwitchProfileManager, EdgeHAProfileManager,
    SiteManager, ComputeSubClusterManager,
    ProjectManager, VPCManager,
    LBServiceManager, LBVirtualServerManager, LBPoolManager,
    LBMonitorProfileManager, LBAppProfileManager,
    LBPersistenceProfileManager, LBSSLProfileManager,
    IPSecVPNManager, L2VPNManager,
    ContextProfileManager, L7AccessProfileManager, IDSIPSManager,
    PredefinedSecurityPolicyManager, FirewallExcludeListManager,
    ClusterSecurityConfigManager,
    IPDiscoveryProfileManager, MACDiscoveryProfileManager,
    SpoofGuardProfileManager, SegmentSecurityProfileManager,
    QoSProfileManager, GatewayQoSProfileManager,
    GatewayFloodProtectionProfileManager,
    EVPNManager,
)
from vcf_sdk.version_check import check_manager_version
from vcf_sdk.versions import NSX_MANAGER_VERSIONS

logger = logging.getLogger(__name__)

# Manager name → class mapping for _init_manager
_NSX_MANAGERS = {
    "segments": SegmentManager,
    "tier0": Tier0Manager,
    "tier1": Tier1Manager,
    "groups": GroupManager,
    "security_policies": SecurityPolicyManager,
    "gateway_policies": GatewayPolicyManager,
    "services": ServiceManager,
    "nat": NATManager,
    "dhcp": DHCPManager,
    "dns": DNSManager,
    "ip_pools": IPPoolManager,
    "transport_zones": TransportZoneManager,
    "edge_clusters": NSXEdgeClusterManager,
    "host_transport_nodes": HostTransportNodeManager,
    "transport_node_collections": TransportNodeCollectionManager,
    "transport_node_profiles": TransportNodeProfileManager,
    "edge_transport_nodes": EdgeTransportNodeManager,
    "host_switch_profiles": HostSwitchProfileManager,
    "edge_ha_profiles": EdgeHAProfileManager,
    "sites": SiteManager,
    "compute_sub_clusters": ComputeSubClusterManager,
    "projects": ProjectManager,
    "vpcs": VPCManager,
    "lb_services": LBServiceManager,
    "lb_virtual_servers": LBVirtualServerManager,
    "lb_pools": LBPoolManager,
    "lb_monitor_profiles": LBMonitorProfileManager,
    "lb_app_profiles": LBAppProfileManager,
    "lb_persistence_profiles": LBPersistenceProfileManager,
    "lb_ssl_profiles": LBSSLProfileManager,
    "ipsec_vpn": IPSecVPNManager,
    "l2vpn": L2VPNManager,
    "context_profiles": ContextProfileManager,
    "l7_access_profiles": L7AccessProfileManager,
    "ids_ips": IDSIPSManager,
    "predefined_policies": PredefinedSecurityPolicyManager,
    "firewall_exclude_list": FirewallExcludeListManager,
    "cluster_security": ClusterSecurityConfigManager,
    "ip_discovery_profiles": IPDiscoveryProfileManager,
    "mac_discovery_profiles": MACDiscoveryProfileManager,
    "spoofguard_profiles": SpoofGuardProfileManager,
    "segment_security_profiles": SegmentSecurityProfileManager,
    "qos_profiles": QoSProfileManager,
    "gateway_qos_profiles": GatewayQoSProfileManager,
    "flood_protection_profiles": GatewayFloodProtectionProfileManager,
    "evpn": EVPNManager,
}


class NSXManager:
    """
    NSX Manager Policy API client — full coverage.

    Attributes:
        version: Detected NSX version string (e.g., "4.2.0")

    All managers are initialized regardless of version. If the connected
    NSX Manager is older than a manager requires, a warning is logged.
    """

    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        verify_ssl: bool = False,
        timeout: int = 30,
    ):
        self.hostname = hostname
        self.client = BaseClient(hostname, verify_ssl=verify_ssl, timeout=timeout)
        self._auth = (username, password)

        # Detect NSX version
        self.version: Optional[str] = self._detect_version()
        if self.version:
            logger.info(f"Connected to NSX Manager {hostname}, version {self.version}")

        # Initialize all managers with version checking
        for name, cls in _NSX_MANAGERS.items():
            setattr(self, name, self._init_manager(name, cls))

    def _detect_version(self) -> Optional[str]:
        """Detect NSX version from the node API."""
        try:
            # The /api/v1/node/version endpoint returns NSX version (Manager API, not Policy)
            url = f"https://{self.hostname}/api/v1/node/version"
            response = self.client.session.request(
                "GET", url,
                auth=self._auth,
                verify=self.client.verify_ssl,
                timeout=self.client.timeout,
            )
            if response.ok:
                data = response.json()
                version = data.get("product_version", "")
                match = re.match(r"(\d+\.\d+\.\d+)", version)
                return match.group(1) if match else version
        except Exception:
            logger.debug("Could not detect NSX version", exc_info=True)
        return None

    def _init_manager(self, name: str, cls):
        """Initialize a manager and check version compatibility."""
        check_manager_version(name, self.version, NSX_MANAGER_VERSIONS, product="NSX")
        mgr = cls(self)
        mgr._api_version = self.version
        return mgr

    def _ensure_policy_path(self, endpoint: str) -> str:
        """Ensure endpoint has /policy/api/v1 prefix."""
        if not endpoint.startswith("/policy"):
            return f"/policy/api/v1{endpoint}"
        return endpoint

    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self.client.request(
            "GET", self._ensure_policy_path(endpoint), auth=self._auth, **kwargs
        )

    def post(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        return self.client.request(
            "POST", self._ensure_policy_path(endpoint), data=data, auth=self._auth, **kwargs
        )

    def put(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        return self.client.request(
            "PUT", self._ensure_policy_path(endpoint), data=data, auth=self._auth, **kwargs
        )

    def patch(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        return self.client.request(
            "PATCH", self._ensure_policy_path(endpoint), data=data, auth=self._auth, **kwargs
        )

    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self.client.request(
            "DELETE", self._ensure_policy_path(endpoint), auth=self._auth, **kwargs
        )

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

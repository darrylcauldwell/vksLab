"""NSX-T Policy API managers."""

from vcf_sdk.nsx.segments import SegmentManager
from vcf_sdk.nsx.tier0 import Tier0Manager
from vcf_sdk.nsx.tier1 import Tier1Manager
from vcf_sdk.nsx.security import GroupManager, SecurityPolicyManager, GatewayPolicyManager
from vcf_sdk.nsx.services import ServiceManager
from vcf_sdk.nsx.nat import NATManager
from vcf_sdk.nsx.dhcp import DHCPManager
from vcf_sdk.nsx.dns import DNSManager
from vcf_sdk.nsx.ip_pools import IPPoolManager
from vcf_sdk.nsx.fabric import (
    TransportZoneManager,
    EdgeClusterManager as NSXEdgeClusterManager,
    HostTransportNodeManager,
    TransportNodeCollectionManager,
    TransportNodeProfileManager,
    EdgeTransportNodeManager,
    HostSwitchProfileManager,
    EdgeHAProfileManager,
    SiteManager,
    ComputeSubClusterManager,
)
from vcf_sdk.nsx.vpc import ProjectManager, VPCManager
from vcf_sdk.nsx.load_balancer import (
    LBServiceManager, LBVirtualServerManager, LBPoolManager,
    LBMonitorProfileManager, LBAppProfileManager,
    LBPersistenceProfileManager, LBSSLProfileManager,
)
from vcf_sdk.nsx.vpn import IPSecVPNManager, L2VPNManager
from vcf_sdk.nsx.evpn import EVPNManager
from vcf_sdk.nsx.advanced_security import (
    ContextProfileManager, L7AccessProfileManager, IDSIPSManager,
    PredefinedSecurityPolicyManager, FirewallExcludeListManager,
    ClusterSecurityConfigManager,
)
from vcf_sdk.nsx.profiles import (
    IPDiscoveryProfileManager, MACDiscoveryProfileManager,
    SpoofGuardProfileManager, SegmentSecurityProfileManager,
    QoSProfileManager, GatewayQoSProfileManager,
    GatewayFloodProtectionProfileManager,
)

__all__ = [
    "SegmentManager", "Tier0Manager", "Tier1Manager",
    "GroupManager", "SecurityPolicyManager", "GatewayPolicyManager",
    "ServiceManager", "NATManager", "DHCPManager", "DNSManager",
    "IPPoolManager", "NSXEdgeClusterManager", "TransportZoneManager",
    "HostTransportNodeManager", "TransportNodeCollectionManager",
    "TransportNodeProfileManager", "EdgeTransportNodeManager",
    "HostSwitchProfileManager", "EdgeHAProfileManager",
    "SiteManager", "ComputeSubClusterManager",
    "ProjectManager", "VPCManager",
    "LBServiceManager", "LBVirtualServerManager", "LBPoolManager",
    "LBMonitorProfileManager", "LBAppProfileManager",
    "LBPersistenceProfileManager", "LBSSLProfileManager",
    "IPSecVPNManager", "L2VPNManager",
    "ContextProfileManager", "L7AccessProfileManager", "IDSIPSManager",
    "PredefinedSecurityPolicyManager", "FirewallExcludeListManager",
    "ClusterSecurityConfigManager",
    "IPDiscoveryProfileManager", "MACDiscoveryProfileManager",
    "SpoofGuardProfileManager", "SegmentSecurityProfileManager",
    "QoSProfileManager", "GatewayQoSProfileManager",
    "GatewayFloodProtectionProfileManager",
    "EVPNManager",
]

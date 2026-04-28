"""API version requirements for VCF SDK.

Maps managers and specific methods to minimum required API versions.
Update this file when new VCF/NSX releases add or deprecate endpoints.

Version format: "major.minor.patch" (e.g., "5.0.0", "9.0.0")
Use None for endpoints available since the API's inception.

Sources:
- SDDC Manager: https://developer.broadcom.com/xapis/sddc-manager-api/latest/
- NSX-T: https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/latest/
- VCF Changelog: techdocs.broadcom.com VCF 9.0 release notes
"""

# --- VCF / SDDC Manager versions ---

# Minimum VCF version for each SDDC Manager manager
SDDC_MANAGER_VERSIONS = {
    # Core (available since VCF 3.x)
    "tasks": None,
    "hosts": None,
    "clusters": None,
    "domains": None,
    "networks": None,
    "images": None,
    "credentials": None,
    "certificates": None,
    "system": None,
    "licenses": None,
    "bundles": None,
    "users": None,
    "edge_clusters": None,
    # VCF 3.9+
    "avns": "3.9.1",
    # VCF 4.0+
    "aria": "4.0.0",
    # VCF 4.2+
    "federation": "4.2.0",
    # VCF 4.3+
    "check_sets": "4.3.0",
    "compatibility": "4.3.0",
    "config_drift": "4.3.0",
    # VCF 4.5+
    "identity_providers": "4.5.0",
    "version_aliases": "4.5.0",
    "vsan": "4.5.0",
    "vasa_providers": "4.5.0",
    # VCF 5.0+
    "brownfield": "5.0.0",
    "trusted_certificates": "5.0.0",
    "resource_functionalities": "5.0.0",
    "vcf_components": "5.0.0",
    "product_binaries": "5.0.0",
    "product_catalogs": "5.0.0",
    "manifests": "5.0.0",
    "notifications": "5.0.0",
    "repository_images": "5.0.0",
    # VCF 5.2+
    "compliance": "5.2.0",
    "alb_clusters": "5.2.0",
}

# Methods within managers that require higher versions than the manager itself
SDDC_METHOD_VERSIONS = {
    # system manager sub-features
    "system.get_vcf_version": None,
    "system.scale_out_nsxt": "5.0.0",
    "system.get_nsxt_projects": "5.2.0",
    "system.get_nsxt_vpc_config": "5.2.0",
    "system.get_nsxt_vpc_profiles": "5.2.0",
    # releases target version features
    "system.list_domain_releases": "5.0.0",
    "system.get_domain_release": "5.0.0",
    "system.set_domain_release": "5.0.0",
    "system.get_future_releases": "5.0.0",
    "system.get_release_components": "5.0.0",
    # users SSO
    "users.list_sso_domains": "4.5.0",
    "users.list_sso_entities": "4.5.0",
    # bundles domain-scoped
    "bundles.get_domain_upgradables": "5.0.0",
    "bundles.preview_upgrade": "5.0.0",
}

# Deprecated features (still work but will be removed)
SDDC_DEPRECATED = {
    "identity_providers": {
        "deprecated_in": "9.0.0",
        "message": "Identity providers are deprecated in VCF 9.0. Use VCF Operations instead.",
    },
}

# --- NSX versions ---

# Minimum NSX version for each NSX manager
NSX_MANAGER_VERSIONS = {
    # Core (NSX-T 2.4+)
    "segments": "2.4.0",
    "tier0": "2.4.0",
    "tier1": "2.4.0",
    "groups": "2.4.0",
    "security_policies": "2.4.0",
    "gateway_policies": "2.4.0",
    "services": "2.4.0",
    "nat": "2.4.0",
    "dhcp": "2.4.0",
    "dns": "2.4.0",
    "ip_pools": "2.4.0",
    "transport_zones": "2.4.0",
    "edge_clusters": "2.4.0",
    # NSX-T 3.0+
    "lb_services": "3.0.0",
    "lb_virtual_servers": "3.0.0",
    "lb_pools": "3.0.0",
    "lb_monitor_profiles": "3.0.0",
    "lb_app_profiles": "3.0.0",
    "lb_persistence_profiles": "3.0.0",
    "lb_ssl_profiles": "3.0.0",
    "context_profiles": "3.0.0",
    "evpn": "3.0.0",
    # NSX-T 3.1+
    "ids_ips": "3.1.0",
    # NSX-T 3.2+
    "flood_protection_profiles": "3.2.0",
    # NSX 4.0+
    "host_transport_nodes": "2.4.0",
    "edge_transport_nodes": "2.4.0",
    "transport_node_profiles": "2.4.0",
    "transport_node_collections": "2.4.0",
    "host_switch_profiles": "2.4.0",
    "edge_ha_profiles": "2.4.0",
    "sites": "3.0.0",
    "compute_sub_clusters": "3.0.0",
    "ip_discovery_profiles": "2.4.0",
    "mac_discovery_profiles": "2.4.0",
    "spoofguard_profiles": "2.4.0",
    "segment_security_profiles": "2.4.0",
    "qos_profiles": "2.4.0",
    "gateway_qos_profiles": "3.0.0",
    "l7_access_profiles": "3.0.0",
    "predefined_policies": "2.4.0",
    "firewall_exclude_list": "2.4.0",
    "cluster_security": "3.0.0",
    # NSX 4.0.1+
    "projects": "4.0.1",
    # NSX 4.1.1+
    "vpcs": "4.1.1",
    # VPN
    "ipsec_vpn": "2.4.0",
    "l2vpn": "2.4.0",
}

# VCF version to bundled NSX version mapping
VCF_TO_NSX = {
    "4.0": "3.0",
    "4.1": "3.0",
    "4.2": "3.1",
    "4.3": "3.1",
    "4.4": "3.2",
    "4.5": "3.2",
    "5.0": "4.1",
    "5.1": "4.1",
    "5.2": "4.2",
    "9.0": "9.0",
}


def parse_version(version_str: str) -> tuple:
    """Parse version string to comparable tuple."""
    if not version_str:
        return (0, 0, 0)
    parts = version_str.split(".")
    return tuple(int(p) for p in parts[:3])


def check_version(current: str, required: str) -> bool:
    """Check if current version meets the required minimum."""
    if required is None:
        return True
    return parse_version(current) >= parse_version(required)

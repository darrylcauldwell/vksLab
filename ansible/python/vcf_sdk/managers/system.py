"""System configuration management."""

import logging
from typing import Any, Dict

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import (
    DNSConfiguration, NTPConfiguration, BackupConfiguration,
    DepotConfiguration, ProxyConfiguration, HealthSummary,
)

logger = logging.getLogger(__name__)


class SystemManager(BaseManager):
    """System configuration: DNS, NTP, backup, CEIP, depot, proxy, health."""

    # System config

    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration."""
        return self._get("/v1/system")

    def update_system_config(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update system configuration."""
        return self._patch("/v1/system", data=spec)

    def get_appliance_info(self) -> Dict[str, Any]:
        """Get appliance information."""
        return self._get("/v1/system/appliance-info")

    # DNS

    def get_dns(self) -> DNSConfiguration:
        """Get DNS configuration."""
        response = self._get("/v1/system/dns-configuration")
        return DNSConfiguration(**response)

    def set_dns(self, spec: Dict[str, Any], validate: bool = True) -> DNSConfiguration:
        """Set DNS configuration."""
        if validate:
            self._validate_and_wait(
                "/v1/system/dns-configuration/validations",
                spec,
            )
        response = self._put("/v1/system/dns-configuration", data=spec)
        return DNSConfiguration(**response)

    # NTP

    def get_ntp(self) -> NTPConfiguration:
        """Get NTP configuration."""
        response = self._get("/v1/system/ntp-configuration")
        return NTPConfiguration(**response)

    def set_ntp(self, spec: Dict[str, Any], validate: bool = True) -> NTPConfiguration:
        """Set NTP configuration."""
        if validate:
            self._validate_and_wait(
                "/v1/system/ntp-configuration/validations",
                spec,
            )
        response = self._put("/v1/system/ntp-configuration", data=spec)
        return NTPConfiguration(**response)

    # Backup

    def get_backup_config(self) -> BackupConfiguration:
        """Get backup configuration."""
        response = self._get("/v1/system/backup-configuration")
        return BackupConfiguration(**response)

    def set_backup_config(self, spec: Dict[str, Any]) -> BackupConfiguration:
        """Set backup configuration."""
        response = self._patch("/v1/system/backup-configuration", data=spec)
        return BackupConfiguration(**response)

    def start_backup(self, spec: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start a backup."""
        return self._post("/v1/backups/tasks", data=spec or {})

    def get_restore_tasks(self) -> Dict[str, Any]:
        """List restore tasks."""
        return self._get("/v1/restores/tasks")

    def start_restore(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Start a restore operation."""
        return self._post("/v1/restores/tasks", data=spec)

    # CEIP

    def get_ceip(self) -> Dict[str, Any]:
        """Get CEIP (Customer Experience Improvement Program) setting."""
        return self._get("/v1/system/ceip")

    def set_ceip(self, enabled: bool) -> Dict[str, Any]:
        """Enable or disable CEIP."""
        setting = "ENABLE" if enabled else "DISABLE"
        return self._patch("/v1/system/ceip", data={"ceipSetting": setting})

    # FIPS

    def get_fips(self) -> Dict[str, Any]:
        """Get FIPS mode status."""
        return self._get("/v1/system/security/fips")

    # Depot

    def get_depot(self) -> DepotConfiguration:
        """Get depot settings."""
        response = self._get("/v1/system/settings/depot")
        return DepotConfiguration(**response)

    def set_depot(self, spec: Dict[str, Any]) -> DepotConfiguration:
        """Set depot settings (VMware account credentials)."""
        response = self._put("/v1/system/settings/depot", data=spec)
        return DepotConfiguration(**response)

    def get_depot_sync_info(self) -> Dict[str, Any]:
        """Get depot sync info."""
        return self._get("/v1/system/settings/depot/depot-sync-info")

    def sync_depot(self, spec: Dict[str, Any] = None) -> Dict[str, Any]:
        """Sync depot metadata."""
        return self._patch("/v1/system/settings/depot/depot-sync-info", data=spec or {})

    # Proxy

    def get_proxy(self) -> ProxyConfiguration:
        """Get proxy configuration."""
        response = self._get("/v1/system/proxy-configuration")
        return ProxyConfiguration(**response)

    def set_proxy(self, spec: Dict[str, Any]) -> ProxyConfiguration:
        """Set proxy configuration."""
        response = self._patch("/v1/system/proxy-configuration", data=spec)
        return ProxyConfiguration(**response)

    # Health & Support

    def start_health_check(self, spec: Dict[str, Any] = None) -> HealthSummary:
        """Start a health check."""
        response = self._post("/v1/system/health-summary", data=spec or {})
        return HealthSummary(**response)

    def get_health_summary(self, check_id: str = None) -> HealthSummary:
        """Get health summary. If check_id provided, get specific check."""
        endpoint = f"/v1/system/health-summary/{check_id}" if check_id else "/v1/system/health-summary"
        response = self._get(endpoint)
        return HealthSummary(**response)

    def download_health_data(self, check_id: str) -> bytes:
        """Download health summary data bundle (tar file)."""
        url = f"https://{self.client.hostname}/v1/system/health-summary/{check_id}/data"
        response = self.client.session.request(
            "GET", url,
            headers={**self.auth.get_auth_headers(), "Accept": "application/octet-stream"},
            verify=self.client.verify_ssl, timeout=self.client.timeout, stream=True,
        )
        response.raise_for_status()
        return response.content

    def start_support_bundle(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Start support bundle generation."""
        return self._post("/v1/system/support-bundles", data=spec)

    def get_support_bundle(self, bundle_id: str) -> Dict[str, Any]:
        """Get support bundle task status."""
        return self._get(f"/v1/system/support-bundles/{bundle_id}")

    def download_support_bundle(self, bundle_id: str) -> bytes:
        """Download support bundle data (tar file)."""
        url = f"https://{self.client.hostname}/v1/system/support-bundles/{bundle_id}/data"
        response = self.client.session.request(
            "GET", url,
            headers={**self.auth.get_auth_headers(), "Accept": "application/octet-stream"},
            verify=self.client.verify_ssl, timeout=self.client.timeout, stream=True,
        )
        response.raise_for_status()
        return response.content

    # Prechecks

    def start_precheck(self, spec: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start a system precheck."""
        return self._post("/v1/system/prechecks", data=spec or {})

    def get_precheck(self, task_id: str) -> Dict[str, Any]:
        """Get precheck task status."""
        return self._get(f"/v1/system/prechecks/tasks/{task_id}")

    # SDDC Manager info

    def list_sddc_managers(self, domain_id: str = None) -> Dict[str, Any]:
        """List SDDC Manager instances, optionally filtered by domain."""
        endpoint = "/v1/sddc-managers"
        if domain_id:
            endpoint += f"?domain={domain_id}"
        return self._get(endpoint)

    def get_sddc_manager(self, manager_id: str) -> Dict[str, Any]:
        """Get SDDC Manager info."""
        return self._get(f"/v1/sddc-managers/{manager_id}")

    def get_vcf_version(self) -> str:
        """Get the VCF version string (e.g., '5.2.0.0')."""
        response = self._get("/v1/sddc-managers")
        elements = response.get("elements", [])
        if elements:
            version = elements[0].get("version", "")
            # Extract x.y.z.b format
            import re
            match = re.match(r"(\d+\.\d+\.\d+\.\d+)", version)
            return match.group(1) if match else version
        return ""

    # Services

    def list_services(self) -> Dict[str, Any]:
        """List VCF services."""
        return self._get("/v1/vcf-services")

    def get_service(self, service_id: str) -> Dict[str, Any]:
        """Get VCF service info."""
        return self._get(f"/v1/vcf-services/{service_id}")

    # PSCs

    def list_pscs(self) -> Dict[str, Any]:
        """List Platform Services Controllers."""
        return self._get("/v1/pscs")

    def get_psc(self, psc_id: str) -> Dict[str, Any]:
        """Get PSC info."""
        return self._get(f"/v1/pscs/{psc_id}")

    # vCenters (read-only from SDDC Manager)

    def list_vcenters(self) -> Dict[str, Any]:
        """List vCenter instances managed by SDDC Manager."""
        return self._get("/v1/vcenters")

    def get_vcenter(self, vcenter_id: str) -> Dict[str, Any]:
        """Get vCenter info."""
        return self._get(f"/v1/vcenters/{vcenter_id}")

    # NSX-T clusters (read-only from SDDC Manager)

    def list_nsxt_clusters(self) -> Dict[str, Any]:
        """List NSX-T clusters managed by SDDC Manager."""
        return self._get("/v1/nsxt-clusters")

    def get_nsxt_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """Get NSX-T cluster info."""
        return self._get(f"/v1/nsxt-clusters/{cluster_id}")

    def scale_out_nsxt(self, cluster_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Scale out NSX cluster."""
        return self._post(f"/v1/nsxt-clusters/{cluster_id}/scale-out", data=spec)

    def query_nsxt_clusters(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Start NSX criteria query."""
        return self._post("/v1/nsxt-clusters/queries", data=spec)

    def get_nsxt_query(self, query_id: str) -> Dict[str, Any]:
        """Get NSX cluster query response."""
        return self._get(f"/v1/nsxt-clusters/queries/{query_id}")

    def connect_nsxt_oidc(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Connect OpenID to NSX."""
        return self._post("/v1/nsxt-clusters/oidcs", data=spec)

    def get_nsxt_criteria(self) -> Dict[str, Any]:
        """Get NSX criteria."""
        return self._get("/v1/nsxt-clusters/criteria")

    def get_nsxt_criterion(self, name: str) -> Dict[str, Any]:
        """Get NSX criterion by name."""
        return self._get(f"/v1/nsxt-clusters/criteria/{name}")

    def get_nsxt_transport_zones(self, cluster_id: str) -> Dict[str, Any]:
        """Get NSX transport zones for a cluster."""
        return self._get(f"/v1/nsxt-clusters/{cluster_id}/transport-zones")

    def get_nsxt_ip_pools(self, cluster_id: str) -> Dict[str, Any]:
        """Get NSX IP address pools for a cluster."""
        return self._get(f"/v1/nsxt-clusters/{cluster_id}/ip-address-pools")

    def get_nsxt_ip_pool(self, cluster_id: str, pool_name: str) -> Dict[str, Any]:
        """Get specific NSX IP address pool."""
        return self._get(f"/v1/nsxt-clusters/{cluster_id}/ip-address-pools/{pool_name}")

    def validate_nsxt_ip_pool(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate NSX IP pool spec."""
        return self._post("/v1/nsxt-clusters/ip-address-pools/validations", data=spec)

    def get_nsxt_ip_pool_validation(self, validation_id: str) -> Dict[str, Any]:
        """Get NSX IP pool validation result."""
        return self._get(f"/v1/nsxt-clusters/ip-address-pools/validations/{validation_id}")

    def get_nsxt_projects(self, cluster_id: str) -> Dict[str, Any]:
        """Get NSX projects for a cluster."""
        return self._get(f"/v1/nsxt-clusters/{cluster_id}/projects")

    def get_nsxt_vpc_profiles(self, cluster_id: str, project_id: str) -> Dict[str, Any]:
        """Get VPC connectivity profiles for a project."""
        return self._get(
            f"/v1/nsxt-clusters/{cluster_id}/projects/{project_id}/vpc-connectivity-profiles"
        )

    def get_nsxt_vpc_config(self, cluster_id: str) -> Dict[str, Any]:
        """Get VPC configuration for a cluster."""
        return self._get(f"/v1/nsxt-clusters/{cluster_id}/vpc-configuration")

    # Releases

    def list_releases(self, **filters) -> Dict[str, Any]:
        """
        List available releases.

        Supported filters: domainId, versionEq, versionGt, productType
        """
        params = [f"{k}={v}" for k, v in filters.items() if v is not None]
        endpoint = "/v1/releases"
        if params:
            endpoint += "?" + "&".join(params)
        return self._get(endpoint)

    def get_system_release(self) -> Dict[str, Any]:
        """Get lowest deployed system release."""
        return self._get("/v1/releases/system")

    def list_domain_releases(self) -> Dict[str, Any]:
        """Get target release view for all domains."""
        return self._get("/v1/releases/domains")

    def get_domain_release(self, domain_id: str) -> Dict[str, Any]:
        """Get target release for a domain."""
        return self._get(f"/v1/releases/domains/{domain_id}")

    def set_domain_release(self, domain_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Modify target upgrade release for a domain."""
        return self._patch(f"/v1/releases/domains/{domain_id}", data=spec)

    def delete_domain_release(self, domain_id: str) -> None:
        """Delete target release for a domain."""
        self._delete(f"/v1/releases/domains/{domain_id}")

    def validate_domain_release(self, domain_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate selected upgrade version for a domain."""
        return self._post(f"/v1/releases/domains/{domain_id}/validations", data=spec)

    def get_domain_release_validation(
        self, domain_id: str, validation_id: str
    ) -> Dict[str, Any]:
        """Get domain target state validation result."""
        return self._get(f"/v1/releases/domains/{domain_id}/validations/{validation_id}")

    def get_future_releases(self, domain_id: str) -> Dict[str, Any]:
        """Get future releases for a domain."""
        return self._get(f"/v1/releases/domains/{domain_id}/future-releases")

    def get_release_components(self, **filters) -> Dict[str, Any]:
        """Get release components by SKU."""
        params = [f"{k}={v}" for k, v in filters.items() if v is not None]
        endpoint = "/v1/releases/sku/release-components"
        if params:
            endpoint += "?" + "&".join(params)
        return self._get(endpoint)

    def get_domain_custom_patches(self, domain_id: str) -> Dict[str, Any]:
        """Get custom patches for a domain."""
        return self._get(f"/v1/releases/domains/{domain_id}/custom-patches")

    def get_custom_patches(self, **filters) -> Dict[str, Any]:
        """Get custom patches by SKU."""
        params = [f"{k}={v}" for k, v in filters.items() if v is not None]
        endpoint = "/v1/releases/custom-patches"
        if params:
            endpoint += "?" + "&".join(params)
        return self._get(endpoint)

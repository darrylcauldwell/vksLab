"""SDDC Manager API client."""

import logging
import re
from typing import Optional

from vcf_sdk.auth import SDDCAuth
from vcf_sdk.base import BaseClient
from vcf_sdk.managers import (
    TaskManager, HostManager, ClusterManager, DomainManager,
    NetworkManager, ImageManager, CredentialManager, CertificateManager,
    SystemManager, LicenseManager, BundleManager, UserManager,
    ComplianceManager, FederationManager, AriaManager, EdgeClusterManager,
    IdentityProviderManager, AVNManager,
    ALBClusterManager, BrownfieldManager, CheckSetManager,
    CompatibilityManager, ConfigDriftManager, ManifestManager,
    NotificationManager, ProductBinaryManager, ProductVersionCatalogManager,
    RepositoryImageManager, ResourceFunctionalityManager,
    TrustedCertificateManager, VASAProviderManager, VCFComponentManager,
    VersionAliasManager, VSANManager,
)
from vcf_sdk.version_check import check_manager_version
from vcf_sdk.versions import SDDC_MANAGER_VERSIONS, SDDC_DEPRECATED

logger = logging.getLogger(__name__)


class SDDCManager:
    """
    SDDC Manager API client — full API coverage.

    Attributes:
        version: Detected VCF version string (e.g., "9.0.2.0")

    All managers are initialized regardless of version. If the connected
    SDDC Manager is older than a manager requires, a warning is logged.
    API calls to unsupported endpoints will return HTTP errors from the server.
    """

    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        verify_ssl: bool = False,
        timeout: int = 30,
    ):
        self.auth = SDDCAuth(hostname, verify_ssl=verify_ssl, timeout=timeout)
        self.client = BaseClient(hostname, verify_ssl=verify_ssl, timeout=timeout)

        # Authenticate
        self.auth.get_token(username, password)

        # Detect VCF version
        self.version: Optional[str] = self._detect_version()
        if self.version:
            logger.info(f"Connected to SDDC Manager {hostname}, VCF version {self.version}")

        # Core managers
        self.tasks = self._init_manager("tasks", TaskManager)
        self.hosts = self._init_manager("hosts", HostManager)
        self.clusters = self._init_manager("clusters", ClusterManager)
        self.domains = self._init_manager("domains", DomainManager)
        self.networks = self._init_manager("networks", NetworkManager)
        self.images = self._init_manager("images", ImageManager)
        self.credentials = self._init_manager("credentials", CredentialManager)
        self.certificates = self._init_manager("certificates", CertificateManager)
        self.system = self._init_manager("system", SystemManager)
        self.licenses = self._init_manager("licenses", LicenseManager)
        self.bundles = self._init_manager("bundles", BundleManager)
        self.users = self._init_manager("users", UserManager)
        self.compliance = self._init_manager("compliance", ComplianceManager)
        self.federation = self._init_manager("federation", FederationManager)
        self.aria = self._init_manager("aria", AriaManager)
        self.edge_clusters = self._init_manager("edge_clusters", EdgeClusterManager)
        self.identity_providers = self._init_manager("identity_providers", IdentityProviderManager)
        self.avns = self._init_manager("avns", AVNManager)

        # Extended managers
        self.alb_clusters = self._init_manager("alb_clusters", ALBClusterManager)
        self.brownfield = self._init_manager("brownfield", BrownfieldManager)
        self.check_sets = self._init_manager("check_sets", CheckSetManager)
        self.compatibility = self._init_manager("compatibility", CompatibilityManager)
        self.config_drift = self._init_manager("config_drift", ConfigDriftManager)
        self.manifests = self._init_manager("manifests", ManifestManager)
        self.notifications = self._init_manager("notifications", NotificationManager)
        self.product_binaries = self._init_manager("product_binaries", ProductBinaryManager)
        self.product_catalogs = self._init_manager("product_catalogs", ProductVersionCatalogManager)
        self.repository_images = self._init_manager("repository_images", RepositoryImageManager)
        self.resource_functionalities = self._init_manager(
            "resource_functionalities", ResourceFunctionalityManager
        )
        self.trusted_certificates = self._init_manager(
            "trusted_certificates", TrustedCertificateManager
        )
        self.vasa_providers = self._init_manager("vasa_providers", VASAProviderManager)
        self.vcf_components = self._init_manager("vcf_components", VCFComponentManager)
        self.version_aliases = self._init_manager("version_aliases", VersionAliasManager)
        self.vsan = self._init_manager("vsan", VSANManager)

    def _detect_version(self) -> Optional[str]:
        """Detect the VCF version from SDDC Manager."""
        try:
            response = self.client.get(
                "/v1/sddc-managers",
                headers=self.auth.get_auth_headers(),
            )
            elements = response.get("elements", [])
            if elements:
                version = elements[0].get("version", "")
                match = re.match(r"(\d+\.\d+\.\d+(?:\.\d+)?)", version)
                return match.group(1) if match else version
        except Exception:
            logger.debug("Could not detect VCF version", exc_info=True)
        return None

    def _init_manager(self, name: str, cls):
        """Initialize a manager and check version compatibility."""
        check_manager_version(
            name, self.version, SDDC_MANAGER_VERSIONS, SDDC_DEPRECATED, product="VCF"
        )
        mgr = cls(self.client, self.auth)
        mgr._api_version = self.version
        return mgr

    def close(self):
        """Close connection."""
        self.auth.close()
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

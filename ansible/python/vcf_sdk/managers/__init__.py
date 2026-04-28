"""SDDC Manager resource managers."""

from vcf_sdk.managers.tasks import TaskManager
from vcf_sdk.managers.hosts import HostManager
from vcf_sdk.managers.clusters import ClusterManager
from vcf_sdk.managers.domains import DomainManager
from vcf_sdk.managers.networks import NetworkManager
from vcf_sdk.managers.images import ImageManager
from vcf_sdk.managers.credentials import CredentialManager
from vcf_sdk.managers.certificates import CertificateManager
from vcf_sdk.managers.system import SystemManager
from vcf_sdk.managers.licensing import LicenseManager
from vcf_sdk.managers.bundles import BundleManager
from vcf_sdk.managers.users import UserManager
from vcf_sdk.managers.compliance import ComplianceManager
from vcf_sdk.managers.federation import FederationManager
from vcf_sdk.managers.aria import AriaManager
from vcf_sdk.managers.edge_clusters import EdgeClusterManager
from vcf_sdk.managers.identity_providers import IdentityProviderManager
from vcf_sdk.managers.avns import AVNManager
from vcf_sdk.managers.alb_clusters import ALBClusterManager
from vcf_sdk.managers.brownfield import BrownfieldManager
from vcf_sdk.managers.check_sets import CheckSetManager
from vcf_sdk.managers.compatibility import CompatibilityManager
from vcf_sdk.managers.config_drift import ConfigDriftManager
from vcf_sdk.managers.manifests import ManifestManager
from vcf_sdk.managers.notifications import NotificationManager
from vcf_sdk.managers.product_catalogs import ProductBinaryManager, ProductVersionCatalogManager
from vcf_sdk.managers.repository_images import RepositoryImageManager
from vcf_sdk.managers.resource_functionalities import ResourceFunctionalityManager
from vcf_sdk.managers.trusted_certs import TrustedCertificateManager
from vcf_sdk.managers.vasa_providers import VASAProviderManager
from vcf_sdk.managers.vcf_components import VCFComponentManager
from vcf_sdk.managers.version_aliases import VersionAliasManager
from vcf_sdk.managers.vsan import VSANManager

__all__ = [
    "TaskManager", "HostManager", "ClusterManager", "DomainManager",
    "NetworkManager", "ImageManager", "CredentialManager", "CertificateManager",
    "SystemManager", "LicenseManager", "BundleManager", "UserManager",
    "ComplianceManager", "FederationManager", "AriaManager", "EdgeClusterManager",
    "IdentityProviderManager", "AVNManager",
    "ALBClusterManager", "BrownfieldManager", "CheckSetManager",
    "CompatibilityManager", "ConfigDriftManager", "ManifestManager",
    "NotificationManager", "ProductBinaryManager", "ProductVersionCatalogManager",
    "RepositoryImageManager", "ResourceFunctionalityManager",
    "TrustedCertificateManager", "VASAProviderManager", "VCFComponentManager",
    "VersionAliasManager", "VSANManager",
]

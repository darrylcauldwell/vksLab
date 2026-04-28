"""Pydantic models for VCF API responses."""

from vcf_sdk.models.task import Task, TaskStatus
from vcf_sdk.models.domain import Domain, DomainSpec
from vcf_sdk.models.host import Host, HostSpec
from vcf_sdk.models.network import NetworkPool, Personality
from vcf_sdk.models.cluster import Cluster, VDS, Validation
from vcf_sdk.models.credential import Credential, CredentialTask
from vcf_sdk.models.certificate import CertificateAuthority, Certificate, CSR
from vcf_sdk.models.system import (
    DNSConfiguration,
    NTPConfiguration,
    BackupConfiguration,
    DepotConfiguration,
    ProxyConfiguration,
    HealthSummary,
)
from vcf_sdk.models.license import LicenseKey, LicensingInfo
from vcf_sdk.models.bundle import Bundle, Upgradable, Upgrade
from vcf_sdk.models.user import User, Role
from vcf_sdk.models.federation import Federation, FederationMember
from vcf_sdk.models.compliance import ComplianceConfiguration, ComplianceAudit
from vcf_sdk.models.aria import AriaLifecycle, AriaOperations, AriaOperationsLogs, AriaAutomation

__all__ = [
    "Task", "TaskStatus",
    "Domain", "DomainSpec",
    "Host", "HostSpec",
    "NetworkPool", "Personality",
    "Cluster", "VDS", "Validation",
    "Credential", "CredentialTask",
    "CertificateAuthority", "Certificate", "CSR",
    "DNSConfiguration", "NTPConfiguration", "BackupConfiguration",
    "DepotConfiguration", "ProxyConfiguration", "HealthSummary",
    "LicenseKey", "LicensingInfo",
    "Bundle", "Upgradable", "Upgrade",
    "User", "Role",
    "Federation", "FederationMember",
    "ComplianceConfiguration", "ComplianceAudit",
    "AriaLifecycle", "AriaOperations", "AriaOperationsLogs", "AriaAutomation",
]

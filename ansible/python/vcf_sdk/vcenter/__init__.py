"""vCenter REST API managers."""

from vcf_sdk.vcenter.vms import VMManager
from vcf_sdk.vcenter.content_library import ContentLibraryManager
from vcf_sdk.vcenter.namespaces import NamespaceManager
from vcf_sdk.vcenter.tagging import TaggingManager
from vcf_sdk.vcenter.infrastructure import InfrastructureManager
from vcf_sdk.vcenter.ovf import OVFManager
from vcf_sdk.vcenter.vm_hardware import VMHardwareManager
from vcf_sdk.vcenter.snapshots import SnapshotManager
from vcf_sdk.vcenter.advanced import DRSRuleManager, FolderManager, GuestCustomizationManager

__all__ = [
    "VMManager", "ContentLibraryManager", "NamespaceManager",
    "TaggingManager", "InfrastructureManager", "OVFManager",
    "VMHardwareManager", "SnapshotManager",
    "DRSRuleManager", "FolderManager", "GuestCustomizationManager",
]

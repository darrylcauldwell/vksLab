"""VCF SDK — Python library for VMware Cloud Foundation automation."""

from vcf_sdk.sddc_manager import SDDCManager
from vcf_sdk.nsx_manager import NSXManager
from vcf_sdk.vcenter_client import VCenter
from vcf_sdk.cloud_builder import CloudBuilder
from vcf_sdk.exceptions import (
    VCFException,
    AuthenticationError,
    ValidationError,
    TaskFailedError,
)

__version__ = "0.2.0"
__all__ = [
    "SDDCManager",
    "NSXManager",
    "VCenter",
    "CloudBuilder",
    "VCFException",
    "AuthenticationError",
    "ValidationError",
    "TaskFailedError",
]

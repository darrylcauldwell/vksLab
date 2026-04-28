"""IP pool models for NSX-T Policy API."""

from typing import Dict, List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class IPPool(NSXResource):
    """IP address pool."""

    pass


class IPPoolSubnet(NSXResource):
    """Static subnet within an IP pool."""

    cidr: Optional[str] = Field(default=None)
    gateway_ip: Optional[str] = Field(default=None)
    allocation_ranges: Optional[List[Dict[str, str]]] = Field(default=None)
    dns_nameservers: Optional[List[str]] = Field(default=None)
    dns_suffix: Optional[str] = Field(default=None)


class IPAllocation(NSXResource):
    """IP allocation from a pool."""

    allocation_ip: Optional[str] = Field(default=None)

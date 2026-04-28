"""VPC multi-tenancy models for NSX-T Policy API (NSX 4.2+)."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class Project(NSXResource):
    """NSX multi-tenancy project."""

    short_id: Optional[str] = Field(default=None)
    tier0s: Optional[List[str]] = Field(default=None)
    site_infos: Optional[List[Dict[str, Any]]] = Field(default=None)
    external_ipv4_blocks: Optional[List[str]] = Field(default=None)


class VPC(NSXResource):
    """NSX VPC (Virtual Private Cloud)."""

    short_id: Optional[str] = Field(default=None)
    ip_address_type: Optional[str] = Field(default=None)
    private_ipv4_blocks: Optional[List[str]] = Field(default=None)
    external_ipv4_blocks: Optional[List[str]] = Field(default=None)
    default_gateway_path: Optional[str] = Field(default=None)
    service_gateway: Optional[Dict[str, Any]] = Field(default=None)
    load_balancer_vpc_endpoint: Optional[Dict[str, Any]] = Field(default=None)


class VPCSubnet(NSXResource):
    """VPC subnet."""

    ipv4_subnet_size: Optional[int] = Field(default=None)
    ip_addresses: Optional[List[str]] = Field(default=None)
    access_mode: Optional[str] = Field(default=None, description="Public, Private, Isolated")
    dhcp_config: Optional[Dict[str, Any]] = Field(default=None)


class VPCSubnetPort(NSXResource):
    """Port on a VPC subnet."""

    attachment: Optional[Dict[str, Any]] = Field(default=None)
    address_bindings: Optional[List[Dict[str, Any]]] = Field(default=None)

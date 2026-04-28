"""NAT rule models for NSX-T Policy API."""

from typing import List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class NATRule(NSXResource):
    """NSX-T NAT rule (SNAT, DNAT, REFLEXIVE, etc.)."""

    action: Optional[str] = Field(
        default=None, description="SNAT, DNAT, REFLEXIVE, NO_SNAT, NO_DNAT, NAT64"
    )
    source_network: Optional[str] = Field(default=None)
    destination_network: Optional[str] = Field(default=None)
    translated_network: Optional[str] = Field(default=None)
    translated_ports: Optional[str] = Field(default=None)
    service: Optional[str] = Field(default=None, description="Service path")
    enabled: Optional[bool] = Field(default=None)
    logging: Optional[bool] = Field(default=None)
    firewall_match: Optional[str] = Field(
        default=None, description="MATCH_INTERNAL_ADDRESS or MATCH_EXTERNAL_ADDRESS"
    )
    sequence_number: Optional[int] = Field(default=None)
    scope: Optional[List[str]] = Field(default=None)

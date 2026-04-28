"""Security models for NSX-T Policy API."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class Group(NSXResource):
    """NSX-T security group with dynamic membership criteria."""

    expression: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Membership expressions (Condition, ConjunctionOperator, IPAddressExpression, etc.)"
    )


class FirewallRule(NSXResource):
    """Firewall rule (used in both security and gateway policies)."""

    action: Optional[str] = Field(default=None, description="ALLOW, DROP, or REJECT")
    source_groups: Optional[List[str]] = Field(default=None, description="Source group paths or ANY")
    destination_groups: Optional[List[str]] = Field(
        default=None, description="Destination group paths or ANY"
    )
    services: Optional[List[str]] = Field(default=None, description="Service paths or ANY")
    profiles: Optional[List[str]] = Field(default=None)
    scope: Optional[List[str]] = Field(default=None)
    logged: Optional[bool] = Field(default=None)
    disabled: Optional[bool] = Field(default=None)
    direction: Optional[str] = Field(default=None, description="IN, OUT, or IN_OUT")
    ip_protocol: Optional[str] = Field(default=None, description="IPV4, IPV6, or IPV4_IPV6")
    sequence_number: Optional[int] = Field(default=None)


class SecurityPolicy(NSXResource):
    """NSX-T distributed firewall security policy."""

    category: Optional[str] = Field(
        default=None,
        description="Ethernet, Emergency, Infrastructure, Environment, or Application"
    )
    scope: Optional[List[str]] = Field(default=None)
    sequence_number: Optional[int] = Field(default=None)
    stateful: Optional[bool] = Field(default=None)
    rules: Optional[List[FirewallRule]] = Field(default=None)


class GatewayPolicy(NSXResource):
    """NSX-T gateway firewall policy."""

    category: Optional[str] = Field(default=None)
    sequence_number: Optional[int] = Field(default=None)
    rules: Optional[List[FirewallRule]] = Field(default=None)


class ServiceEntry(NSXResource):
    """Service entry (L4 port definition within a service)."""

    l4_protocol: Optional[str] = Field(default=None, description="TCP or UDP")
    destination_ports: Optional[List[str]] = Field(default=None)
    source_ports: Optional[List[str]] = Field(default=None)


class Service(NSXResource):
    """NSX-T service (collection of L4 port definitions)."""

    service_entries: Optional[List[ServiceEntry]] = Field(default=None)

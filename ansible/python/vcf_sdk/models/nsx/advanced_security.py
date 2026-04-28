"""Advanced security models (context profiles, IDS/IPS) for NSX-T Policy API."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from vcf_sdk.models.nsx.base import NSXResource


class ContextProfile(NSXResource):
    """L7 context profile for application identification."""

    attributes: Optional[List[Dict[str, Any]]] = Field(default=None)


class ContextProfileCustomAttribute(NSXResource):
    """Custom attribute for context profiles."""

    attribute_source: Optional[str] = Field(default=None)
    custom_url_partial_match: Optional[bool] = Field(default=None)
    sub_attributes: Optional[List[Dict[str, Any]]] = Field(default=None)


class L7AccessProfile(NSXResource):
    """L7 access profile."""

    l7_access_entries: Optional[List[Dict[str, Any]]] = Field(default=None)


class IntrusionServicePolicy(NSXResource):
    """IDS/IPS distributed intrusion service policy."""

    rules: Optional[List[Dict[str, Any]]] = Field(default=None)
    scope: Optional[List[str]] = Field(default=None)
    sequence_number: Optional[int] = Field(default=None)
    stateful: Optional[bool] = Field(default=None)


class IntrusionServiceProfile(NSXResource):
    """IDS/IPS profile defining signature overrides."""

    overridden_signatures: Optional[List[Dict[str, Any]]] = Field(default=None)
    criteria: Optional[List[Dict[str, Any]]] = Field(default=None)


class IntrusionServiceGatewayPolicy(NSXResource):
    """IDS/IPS gateway policy."""

    rules: Optional[List[Dict[str, Any]]] = Field(default=None)
    scope: Optional[List[str]] = Field(default=None)
    sequence_number: Optional[int] = Field(default=None)


class IDSSettings(NSXResource):
    """Global IDS/IPS settings."""

    auto_update: Optional[bool] = Field(default=None)


class IDSSignatureVersion(NSXResource):
    """IDS/IPS signature version."""

    version_id: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)

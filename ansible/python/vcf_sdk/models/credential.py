"""Credential models for SDDC Manager API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Credential(BaseModel):
    """SDDC Manager credential response model."""

    id: str = Field(description="Credential UUID")
    resource_name: Optional[str] = Field(default=None, alias="resourceName")
    resource_type: Optional[str] = Field(
        default=None, alias="resourceType",
        description="VCENTER, ESXI, NSXT_MANAGER, NSXT_EDGE, etc."
    )
    resource_ip: Optional[str] = Field(default=None, alias="resourceIp")
    credential_type: Optional[str] = Field(
        default=None, alias="credentialType",
        description="SSH, API, SSO, etc."
    )
    account_type: Optional[str] = Field(
        default=None, alias="accountType",
        description="USER, SYSTEM, SERVICE"
    )
    username: Optional[str] = Field(default=None)
    domain_name: Optional[str] = Field(default=None, alias="domainName")
    creation_time: Optional[str] = Field(default=None, alias="creationTime")
    modification_time: Optional[str] = Field(default=None, alias="modificationTime")

    model_config = ConfigDict(populate_by_name=True)


class CredentialTask(BaseModel):
    """Credential operation task."""

    id: str = Field(description="Credential task ID")
    status: Optional[str] = Field(default=None)
    credential_type: Optional[str] = Field(default=None, alias="credentialType")
    sub_tasks: Optional[List[Dict[str, Any]]] = Field(default=None, alias="subTasks")

    model_config = ConfigDict(populate_by_name=True)

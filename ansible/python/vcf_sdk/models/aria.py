"""Aria Suite (vRealize) models for SDDC Manager API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AriaLifecycle(BaseModel):
    """Aria Suite Lifecycle Manager response model."""

    id: Optional[str] = Field(default=None)
    fqdn: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    version: Optional[str] = Field(default=None)
    api_url: Optional[str] = Field(default=None, alias="apiUrl")

    model_config = ConfigDict(populate_by_name=True)


class AriaOperations(BaseModel):
    """Aria Operations (vROps) response model."""

    id: Optional[str] = Field(default=None)
    fqdn: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    version: Optional[str] = Field(default=None)
    nodes: Optional[List[Dict[str, Any]]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class AriaOperationsLogs(BaseModel):
    """Aria Operations for Logs (vRLI) response model."""

    id: Optional[str] = Field(default=None)
    fqdn: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    version: Optional[str] = Field(default=None)
    nodes: Optional[List[Dict[str, Any]]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class AriaAutomation(BaseModel):
    """Aria Automation (vRA) response model."""

    id: Optional[str] = Field(default=None)
    fqdn: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    version: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)

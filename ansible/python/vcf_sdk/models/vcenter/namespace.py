"""Namespace management models for vCenter REST API (Tanzu/VKS)."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SupervisorCluster(BaseModel):
    """Supervisor-enabled cluster."""

    cluster: Optional[str] = Field(default=None, description="Cluster identifier")
    cluster_name: Optional[str] = Field(default=None)
    config_status: Optional[str] = Field(default=None, description="CONFIGURING, RUNNING, ERROR, etc.")
    kubernetes_status: Optional[str] = Field(default=None, description="READY, WARNING, ERROR")
    stats: Optional[Dict[str, Any]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class Namespace(BaseModel):
    """vSphere Namespace."""

    namespace: Optional[str] = Field(default=None, description="Namespace name")
    cluster: Optional[str] = Field(default=None, description="Cluster identifier")
    description: Optional[str] = Field(default=None)
    config_status: Optional[str] = Field(default=None)
    stats: Optional[Dict[str, Any]] = Field(default=None)
    storage_specs: Optional[List[Dict[str, Any]]] = Field(default=None)
    access_list: Optional[List[Dict[str, Any]]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class NamespaceAccess(BaseModel):
    """Namespace access/permission entry."""

    subject_type: Optional[str] = Field(default=None, description="USER, GROUP")
    subject: Optional[str] = Field(default=None)
    domain: Optional[str] = Field(default=None)
    role: Optional[str] = Field(default=None, description="EDIT, VIEW")

    model_config = ConfigDict(populate_by_name=True)

"""Cluster models for SDDC Manager API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class VDS(BaseModel):
    """Virtual Distributed Switch response model."""

    id: str = Field(description="VDS UUID")
    name: str = Field(description="VDS name")
    mtu: Optional[int] = Field(default=None, description="MTU setting")
    is_used: Optional[bool] = Field(default=None, alias="isUsed")
    niocs: Optional[List[Dict[str, Any]]] = Field(default=None, description="NIOC specs")
    port_groups: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="portGroups", description="Port groups"
    )

    model_config = ConfigDict(populate_by_name=True)


class Cluster(BaseModel):
    """SDDC Manager cluster response model."""

    id: str = Field(description="Cluster UUID")
    name: str = Field(description="Cluster name")
    status: str = Field(description="Cluster status")
    primary_datastore_name: Optional[str] = Field(
        default=None, alias="primaryDatastoreName"
    )
    primary_datastore_type: Optional[str] = Field(
        default=None, alias="primaryDatastoreType"
    )
    is_default: Optional[bool] = Field(default=None, alias="isDefault")
    is_stretched: Optional[bool] = Field(default=None, alias="isStretched")
    host_count: Optional[int] = Field(default=None, alias="hostCount")
    hosts: Optional[List[Dict[str, Any]]] = Field(default=None)
    domain_id: Optional[str] = Field(default=None, alias="domainId")
    vds: Optional[List[VDS]] = Field(default=None, description="Virtual Distributed Switches")

    model_config = ConfigDict(populate_by_name=True)


class Validation(BaseModel):
    """Validation response from /validations endpoints."""

    id: str = Field(description="Validation ID")
    execution_status: Optional[str] = Field(
        default=None, alias="executionStatus", description="COMPLETED, IN_PROGRESS, etc."
    )
    result_status: Optional[str] = Field(
        default=None, alias="resultStatus", description="SUCCEEDED, FAILED"
    )
    validation_checks: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="validationChecks"
    )

    model_config = ConfigDict(populate_by_name=True)

    @property
    def is_complete(self) -> bool:
        return self.execution_status == "COMPLETED"

    @property
    def is_successful(self) -> bool:
        return self.is_complete and self.result_status == "SUCCEEDED"

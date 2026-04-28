"""Domain models for SDDC Manager API."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class DomainSpec(BaseModel):
    """VI workload domain creation specification."""

    domain_name: str = Field(alias="domainName", description="Domain name")
    vcenter_spec: Dict[str, Any] = Field(
        alias="vcenterSpec",
        description="vCenter configuration",
    )
    compute_spec: Dict[str, Any] = Field(
        alias="computeSpec",
        description="Cluster and compute configuration",
    )
    nsx_t_spec: Dict[str, Any] = Field(
        alias="nsxTSpec",
        description="NSX Manager configuration",
    )

    model_config = ConfigDict(populate_by_name=True)


class Domain(BaseModel):
    """SDDC Manager domain response model."""

    id: str = Field(description="Domain UUID")
    name: str = Field(description="Domain name")
    status: str = Field(description="Domain status (ACTIVE, PROVISIONING, etc.)")
    cluster_count: Optional[int] = Field(
        default=None,
        alias="clusterCount",
        description="Number of clusters in domain",
    )
    host_count: Optional[int] = Field(
        default=None,
        alias="hostCount",
        description="Number of hosts in domain",
    )
    vcenter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="vCenter details",
    )
    nsx_t: Optional[Dict[str, Any]] = Field(
        default=None,
        alias="nsxT",
        description="NSX Manager details",
    )

    model_config = ConfigDict(populate_by_name=True)

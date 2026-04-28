"""Host models for SDDC Manager API."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class HostSpec(BaseModel):
    """Host commissioning specification."""

    fqdn: str = Field(description="Host FQDN")
    username: str = Field(description="Host SSH username")
    password: str = Field(description="Host SSH password")
    storage_type: str = Field(alias="storageType", description="Storage type (VSAN_ESA, VSAN)")
    network_pool_id: Optional[str] = Field(
        default=None,
        alias="networkPoolId",
        description="Network pool UUID for IP allocation",
    )

    model_config = ConfigDict(populate_by_name=True)


class Host(BaseModel):
    """SDDC Manager host response model."""

    id: str = Field(description="Host UUID")
    fqdn: str = Field(description="Host FQDN")
    status: str = Field(description="Host status (COMMISSIONED, DECOMMISSIONED, etc.)")
    cluster_id: Optional[str] = Field(
        default=None,
        alias="clusterId",
        description="Cluster ID if assigned",
    )
    cluster_name: Optional[str] = Field(
        default=None,
        alias="clusterName",
        description="Cluster name if assigned",
    )
    storage_type: Optional[str] = Field(
        default=None,
        alias="storageType",
        description="Storage type (VSAN_ESA, VSAN)",
    )
    ipv4_address: Optional[str] = Field(
        default=None,
        alias="ipv4Address",
        description="Management IPv4 address",
    )
    hardware: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Hardware details",
    )

    model_config = ConfigDict(populate_by_name=True)

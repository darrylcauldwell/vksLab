"""Infrastructure models (cluster, datacenter, datastore, host, network) for vCenter REST API."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Cluster(BaseModel):
    """Cluster summary."""

    cluster: Optional[str] = Field(default=None, description="Cluster identifier")
    name: Optional[str] = Field(default=None)
    ha_enabled: Optional[bool] = Field(default=None)
    drs_enabled: Optional[bool] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class Datacenter(BaseModel):
    """Datacenter summary."""

    datacenter: Optional[str] = Field(default=None, description="Datacenter identifier")
    name: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class Datastore(BaseModel):
    """Datastore summary."""

    datastore: Optional[str] = Field(default=None, description="Datastore identifier")
    name: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None, description="VMFS, NFS, VSAN, VVOL")
    free_space: Optional[int] = Field(default=None)
    capacity: Optional[int] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class HostSummary(BaseModel):
    """Host summary."""

    host: Optional[str] = Field(default=None, description="Host identifier")
    name: Optional[str] = Field(default=None)
    connection_state: Optional[str] = Field(default=None, description="CONNECTED, DISCONNECTED, NOT_RESPONDING")
    power_state: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class Network(BaseModel):
    """Network summary."""

    network: Optional[str] = Field(default=None, description="Network identifier")
    name: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None, description="STANDARD_PORTGROUP, DISTRIBUTED_PORTGROUP, OPAQUE_NETWORK")

    model_config = ConfigDict(populate_by_name=True)


class ResourcePool(BaseModel):
    """Resource pool summary."""

    resource_pool: Optional[str] = Field(default=None, description="Resource pool identifier")
    name: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class StoragePolicy(BaseModel):
    """Storage policy."""

    policy: Optional[str] = Field(default=None, description="Policy identifier")
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)

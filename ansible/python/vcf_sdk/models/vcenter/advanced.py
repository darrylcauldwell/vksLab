"""Advanced vCenter models — VM hardware, snapshots, DRS, folders, permissions."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class VMDisk(BaseModel):
    """VM disk info."""

    label: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    capacity: Optional[int] = Field(default=None)
    backing: Optional[Dict[str, Any]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class VMNIC(BaseModel):
    """VM network interface."""

    label: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    mac_address: Optional[str] = Field(default=None)
    mac_type: Optional[str] = Field(default=None)
    state: Optional[str] = Field(default=None)
    backing: Optional[Dict[str, Any]] = Field(default=None)
    start_connected: Optional[bool] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class VMCdrom(BaseModel):
    """VM CD-ROM."""

    label: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    backing: Optional[Dict[str, Any]] = Field(default=None)
    state: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class Snapshot(BaseModel):
    """VM snapshot."""

    snapshot: Optional[str] = Field(default=None, description="Snapshot identifier")
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    parent: Optional[str] = Field(default=None)
    children: Optional[List[Dict[str, Any]]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class DRSRule(BaseModel):
    """DRS rule (affinity/anti-affinity)."""

    rule: Optional[str] = Field(default=None, description="Rule identifier")
    name: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None, description="AFFINITY, ANTI_AFFINITY, etc.")
    enabled: Optional[bool] = Field(default=None)
    vms: Optional[List[str]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class Folder(BaseModel):
    """vCenter folder."""

    folder: Optional[str] = Field(default=None, description="Folder identifier")
    name: Optional[str] = Field(default=None)
    type: Optional[str] = Field(
        default=None, description="DATACENTER, HOST, NETWORK, DATASTORE, VIRTUAL_MACHINE"
    )

    model_config = ConfigDict(populate_by_name=True)

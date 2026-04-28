"""VM models for vCenter REST API."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class VM(BaseModel):
    """VM summary from list endpoint."""

    vm: str = Field(description="VM identifier (e.g., vm-42)")
    name: str = Field(description="VM name")
    power_state: Optional[str] = Field(default=None, description="POWERED_ON, POWERED_OFF, SUSPENDED")
    cpu_count: Optional[int] = Field(default=None)
    memory_size_MiB: Optional[int] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class VMDetail(BaseModel):
    """Detailed VM info from get endpoint."""

    name: Optional[str] = Field(default=None)
    power_state: Optional[str] = Field(default=None)
    cpu: Optional[Dict[str, Any]] = Field(default=None)
    memory: Optional[Dict[str, Any]] = Field(default=None)
    disks: Optional[Dict[str, Any]] = Field(default=None)
    nics: Optional[Dict[str, Any]] = Field(default=None)
    cdroms: Optional[Dict[str, Any]] = Field(default=None)
    guest_OS: Optional[str] = Field(default=None)
    hardware: Optional[Dict[str, Any]] = Field(default=None)
    boot: Optional[Dict[str, Any]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)

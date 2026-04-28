"""OVF deployment models for vCenter REST API."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class OVFDeployResult(BaseModel):
    """Result of OVF library item deployment."""

    succeeded: Optional[bool] = Field(default=None)
    resource_id: Optional[Dict[str, str]] = Field(default=None, description="{'type': 'VirtualMachine', 'id': 'vm-100'}")
    error: Optional[Dict[str, Any]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)

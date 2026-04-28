"""User and role models for SDDC Manager API."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """SDDC Manager user response model."""

    id: str = Field(description="User UUID")
    name: str = Field(description="Username")
    domain: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None, description="USER or SERVICE")
    role: Optional[Dict[str, Any]] = Field(default=None)
    creation_time: Optional[str] = Field(default=None, alias="creationTime")

    model_config = ConfigDict(populate_by_name=True)


class Role(BaseModel):
    """SDDC Manager role response model."""

    id: str = Field(description="Role UUID")
    name: str = Field(description="Role name")
    description: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)

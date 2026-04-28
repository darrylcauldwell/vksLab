"""Federation models for SDDC Manager API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Federation(BaseModel):
    """SDDC Federation response model."""

    controller_role: Optional[str] = Field(default=None, alias="controllerRole")
    member_role: Optional[str] = Field(default=None, alias="memberRole")
    sddc_managers: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="sddcManagers"
    )

    model_config = ConfigDict(populate_by_name=True)


class FederationMember(BaseModel):
    """Federation member response model."""

    id: Optional[str] = Field(default=None)
    fqdn: Optional[str] = Field(default=None)
    role: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)

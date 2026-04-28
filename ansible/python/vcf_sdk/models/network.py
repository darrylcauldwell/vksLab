"""Network models for SDDC Manager and NSX API responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class NetworkPool(BaseModel):
    """SDDC Manager network pool response model."""

    id: str = Field(description="Network pool UUID")
    name: str = Field(description="Network pool name")
    hosts_count: Optional[int] = Field(
        default=None,
        alias="hostsCount",
        description="Number of hosts in pool",
    )
    networks: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Network IDs in pool",
    )

    model_config = ConfigDict(populate_by_name=True)


class Personality(BaseModel):
    """vLCM image (personality) response model."""

    personality_id: str = Field(alias="personalityId", description="Image UUID")
    personality_name: str = Field(
        alias="personalityName",
        description="Image name (e.g., Management-Domain-ESXi-Personality)",
    )
    base_image_version: str = Field(
        alias="baseImageVersion",
        description="Base image version (e.g., 9.0.2-24xxxxxx)",
    )
    add_on: Optional[Dict[str, Any]] = Field(default=None, description="Add-on details")
    components: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Component details",
    )

    model_config = ConfigDict(populate_by_name=True)

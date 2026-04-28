"""Bundle and upgrade models for SDDC Manager API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Bundle(BaseModel):
    """Lifecycle bundle response model."""

    id: str = Field(description="Bundle UUID")
    bundle_type: Optional[str] = Field(default=None, alias="bundleType")
    description: Optional[str] = Field(default=None)
    version: Optional[str] = Field(default=None)
    download_status: Optional[str] = Field(default=None, alias="downloadStatus")
    components: Optional[List[Dict[str, Any]]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class Upgradable(BaseModel):
    """Upgradable resource response model."""

    resource_id: Optional[str] = Field(default=None, alias="resourceId")
    resource_name: Optional[str] = Field(default=None, alias="resourceName")
    resource_type: Optional[str] = Field(default=None, alias="resourceType")
    current_version: Optional[str] = Field(default=None, alias="currentVersion")
    target_version: Optional[str] = Field(default=None, alias="targetVersion")
    status: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class Upgrade(BaseModel):
    """Upgrade response model."""

    id: str = Field(description="Upgrade UUID")
    status: Optional[str] = Field(default=None)
    upgrade_units: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="upgradeUnits"
    )

    model_config = ConfigDict(populate_by_name=True)

"""License models for SDDC Manager API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LicenseKey(BaseModel):
    """License key response model."""

    key: str = Field(description="License key")
    description: Optional[str] = Field(default=None)
    product_type: Optional[str] = Field(
        default=None, alias="productType",
        description="VCENTER, ESXI, VSAN, NSXT, etc."
    )
    license_key_status: Optional[str] = Field(
        default=None, alias="licenseKeyStatus",
        description="ACTIVE, EXPIRED, etc."
    )
    license_key_usage: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="licenseKeyUsage"
    )

    model_config = ConfigDict(populate_by_name=True)


class LicensingInfo(BaseModel):
    """Licensing info summary."""

    licensing_mode: Optional[str] = Field(default=None, alias="licensingMode")

    model_config = ConfigDict(populate_by_name=True)

"""Compliance models for SDDC Manager API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ComplianceConfiguration(BaseModel):
    """Compliance configuration response model."""

    id: Optional[str] = Field(default=None)
    configurations: Optional[List[Dict[str, Any]]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class ComplianceAudit(BaseModel):
    """Compliance audit response model."""

    id: str = Field(description="Audit UUID")
    status: Optional[str] = Field(default=None)
    audit_results: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="auditResults"
    )

    model_config = ConfigDict(populate_by_name=True)

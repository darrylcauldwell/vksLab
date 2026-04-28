"""Tagging models for vCenter REST API."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TagCategory(BaseModel):
    """Tag category."""

    id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    cardinality: Optional[str] = Field(default=None, description="SINGLE or MULTIPLE")
    associable_types: Optional[List[str]] = Field(default=None)
    used_by: Optional[List[str]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class Tag(BaseModel):
    """Tag."""

    id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    category_id: Optional[str] = Field(default=None)
    used_by: Optional[List[str]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)

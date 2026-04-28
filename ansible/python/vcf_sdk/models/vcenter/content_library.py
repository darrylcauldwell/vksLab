"""Content Library models for vCenter REST API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Library(BaseModel):
    """Content library."""

    id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None, description="LOCAL or SUBSCRIBED")
    storage_backings: Optional[List[Dict[str, Any]]] = Field(default=None)
    publish_info: Optional[Dict[str, Any]] = Field(default=None)
    subscription_info: Optional[Dict[str, Any]] = Field(default=None)
    creation_time: Optional[str] = Field(default=None)
    last_modified_time: Optional[str] = Field(default=None)
    version: Optional[str] = Field(default=None)
    server_guid: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class LibraryItem(BaseModel):
    """Content library item."""

    id: Optional[str] = Field(default=None)
    library_id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None, description="ovf, iso, vm-template, etc.")
    size: Optional[int] = Field(default=None)
    creation_time: Optional[str] = Field(default=None)
    last_modified_time: Optional[str] = Field(default=None)
    version: Optional[str] = Field(default=None)
    content_version: Optional[str] = Field(default=None)
    cached: Optional[bool] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)

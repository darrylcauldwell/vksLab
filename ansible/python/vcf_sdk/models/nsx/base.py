"""Base model for NSX Policy API resources."""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class NSXResource(BaseModel):
    """Base model for all NSX Policy API resources.

    NSX Policy API uses snake_case natively, so minimal aliasing needed.
    Common fields: id, display_name, description, tags, path, resource_type, _revision.
    """

    id: Optional[str] = Field(default=None, description="Resource ID (user-defined)")
    display_name: Optional[str] = Field(default=None, description="Display name")
    description: Optional[str] = Field(default=None)
    resource_type: Optional[str] = Field(default=None, description="NSX resource type")
    path: Optional[str] = Field(default=None, description="Policy path")
    tags: Optional[List[Dict[str, str]]] = Field(default=None, description="NSX tags")
    revision: Optional[int] = Field(default=None, alias="_revision")

    model_config = ConfigDict(populate_by_name=True)

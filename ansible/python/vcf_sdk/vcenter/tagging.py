"""Tagging management for vCenter REST API."""

from typing import Any, Dict, List

from vcf_sdk.models.vcenter import TagCategory, Tag
from vcf_sdk.vcenter.base import VCBaseManager


class TaggingManager(VCBaseManager):
    """Manage tag categories, tags, and tag associations."""

    # Categories

    def list_categories(self) -> List[str]:
        """List category IDs."""
        return self._raw_get("/cis/tagging/category") or []

    def get_category(self, category_id: str) -> TagCategory:
        """Get category details."""
        return self._get(f"/cis/tagging/category/{category_id}", TagCategory)

    def create_category(self, spec: Dict[str, Any]) -> str:
        """Create a category. Returns category ID."""
        return self._post("/cis/tagging/category", data=spec)

    def update_category(self, category_id: str, spec: Dict[str, Any]) -> None:
        """Update a category."""
        self._patch(f"/cis/tagging/category/{category_id}", data=spec)

    def delete_category(self, category_id: str) -> None:
        """Delete a category."""
        self._delete(f"/cis/tagging/category/{category_id}")

    # Tags

    def list_tags(self) -> List[str]:
        """List tag IDs."""
        return self._raw_get("/cis/tagging/tag") or []

    def get_tag(self, tag_id: str) -> Tag:
        """Get tag details."""
        return self._get(f"/cis/tagging/tag/{tag_id}", Tag)

    def create_tag(self, spec: Dict[str, Any]) -> str:
        """Create a tag. Returns tag ID."""
        return self._post("/cis/tagging/tag", data=spec)

    def update_tag(self, tag_id: str, spec: Dict[str, Any]) -> None:
        """Update a tag."""
        self._patch(f"/cis/tagging/tag/{tag_id}", data=spec)

    def delete_tag(self, tag_id: str) -> None:
        """Delete a tag."""
        self._delete(f"/cis/tagging/tag/{tag_id}")

    # Tag Associations

    def attach(self, tag_id: str, object_type: str, object_id: str) -> None:
        """Attach a tag to an object."""
        self._post("/cis/tagging/tag-association?action=attach", data={
            "tag_id": tag_id,
            "object_id": {"type": object_type, "id": object_id},
        })

    def detach(self, tag_id: str, object_type: str, object_id: str) -> None:
        """Detach a tag from an object."""
        self._post("/cis/tagging/tag-association?action=detach", data={
            "tag_id": tag_id,
            "object_id": {"type": object_type, "id": object_id},
        })

    def list_attached_tags(self, object_type: str, object_id: str) -> List[str]:
        """List tag IDs attached to an object."""
        return self._post("/cis/tagging/tag-association?action=list-attached-tags", data={
            "object_id": {"type": object_type, "id": object_id},
        }) or []

    def list_attached_objects(self, tag_id: str) -> List[Dict[str, str]]:
        """List objects attached to a tag."""
        return self._post(
            "/cis/tagging/tag-association?action=list-attached-objects",
            data={"tag_id": tag_id},
        ) or []

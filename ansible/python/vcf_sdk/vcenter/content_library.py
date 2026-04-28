"""Content Library management for vCenter REST API."""

from typing import Any, Dict, List

from vcf_sdk.models.vcenter import Library, LibraryItem
from vcf_sdk.vcenter.base import VCBaseManager


class ContentLibraryManager(VCBaseManager):
    """Manage content libraries and library items."""

    # Local Libraries

    def list_local_libraries(self) -> List[str]:
        """List local library IDs."""
        return self._raw_get("/content/local-library") or []

    def get_local_library(self, library_id: str) -> Library:
        """Get local library details."""
        return self._get(f"/content/local-library/{library_id}", Library)

    def create_local_library(self, spec: Dict[str, Any]) -> str:
        """Create a local library. Returns library ID."""
        return self._post("/content/local-library", data=spec)

    def update_local_library(self, library_id: str, spec: Dict[str, Any]) -> None:
        """Update a local library."""
        self._patch(f"/content/local-library/{library_id}", data=spec)

    def delete_local_library(self, library_id: str) -> None:
        """Delete a local library."""
        self._delete(f"/content/local-library/{library_id}")

    # Subscribed Libraries

    def list_subscribed_libraries(self) -> List[str]:
        """List subscribed library IDs."""
        return self._raw_get("/content/subscribed-library") or []

    def get_subscribed_library(self, library_id: str) -> Library:
        """Get subscribed library details."""
        return self._get(f"/content/subscribed-library/{library_id}", Library)

    def create_subscribed_library(self, spec: Dict[str, Any]) -> str:
        """Create a subscribed library. Returns library ID."""
        return self._post("/content/subscribed-library", data=spec)

    def sync_subscribed_library(self, library_id: str) -> None:
        """Sync a subscribed library."""
        self._post(f"/content/subscribed-library/{library_id}?action=sync")

    def delete_subscribed_library(self, library_id: str) -> None:
        """Delete a subscribed library."""
        self._delete(f"/content/subscribed-library/{library_id}")

    # Library Items

    def list_items(self, library_id: str) -> List[str]:
        """List item IDs in a library."""
        return self._raw_get(f"/content/library/item?library_id={library_id}") or []

    def get_item(self, item_id: str) -> LibraryItem:
        """Get library item details."""
        return self._get(f"/content/library/item/{item_id}", LibraryItem)

    def create_item(self, spec: Dict[str, Any]) -> str:
        """Create a library item. Returns item ID."""
        return self._post("/content/library/item", data=spec)

    def update_item(self, item_id: str, spec: Dict[str, Any]) -> None:
        """Update a library item."""
        self._patch(f"/content/library/item/{item_id}", data=spec)

    def delete_item(self, item_id: str) -> None:
        """Delete a library item."""
        self._delete(f"/content/library/item/{item_id}")

    def publish_item(self, item_id: str) -> None:
        """Publish a library item to subscribers."""
        self._post(f"/content/library/item/{item_id}?action=publish")

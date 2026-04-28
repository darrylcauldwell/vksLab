"""vCenter REST API client."""

import json
import logging
from typing import Any

from vcf_sdk.base import BaseClient
from vcf_sdk.exceptions import VCFException
from vcf_sdk.vcenter_auth import VCenterAuth
from vcf_sdk.vcenter import (
    VMManager,
    ContentLibraryManager,
    NamespaceManager,
    TaggingManager,
    InfrastructureManager,
    OVFManager,
    VMHardwareManager,
    SnapshotManager,
    DRSRuleManager,
    FolderManager,
    GuestCustomizationManager,
)

logger = logging.getLogger(__name__)


class VCenter:
    """
    vCenter REST API client.

    Provides access to all vCenter REST API managers:
        vms, content_library, namespaces, tagging,
        infrastructure, ovf
    """

    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        verify_ssl: bool = False,
        timeout: int = 30,
    ):
        self.hostname = hostname
        self.auth = VCenterAuth(hostname, verify_ssl=verify_ssl, timeout=timeout)
        self.client = BaseClient(hostname, verify_ssl=verify_ssl, timeout=timeout)

        # Authenticate
        self.auth.login(username, password)

        # Initialize managers
        self.vms = VMManager(self)
        self.content_library = ContentLibraryManager(self)
        self.namespaces = NamespaceManager(self)
        self.tagging = TaggingManager(self)
        self.infrastructure = InfrastructureManager(self)
        self.ovf = OVFManager(self)
        self.vm_hardware = VMHardwareManager(self)
        self.snapshots = SnapshotManager(self)
        self.drs_rules = DRSRuleManager(self)
        self.folders = FolderManager(self)
        self.guest_customization = GuestCustomizationManager(self)

    def _ensure_api_path(self, endpoint: str) -> str:
        """Ensure endpoint has /api/ prefix."""
        if not endpoint.startswith("/api"):
            return f"/api{endpoint}"
        return endpoint

    def _handle_response(self, response) -> Any:
        """Handle vCenter response — may be JSON array, object, string, or empty."""
        if response.status_code == 204:
            return None
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()
        # Some endpoints return bare strings
        text = response.text.strip()
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return None

    def _request(self, method: str, endpoint: str, data: Any = None, **kwargs) -> Any:
        """Make authenticated request to vCenter API."""
        url = f"https://{self.hostname}{self._ensure_api_path(endpoint)}"
        headers = {
            "Content-Type": "application/json",
            **self.auth.get_session_headers(),
        }
        req_kwargs = {"headers": headers, "verify": self.client.verify_ssl, "timeout": self.client.timeout}
        if data is not None:
            req_kwargs["data"] = json.dumps(data)
        req_kwargs.update(kwargs)

        response = self.client.session.request(method, url, **req_kwargs)

        if response.status_code == 401:
            # Session expired — re-authenticate and retry
            logger.debug("Session expired, re-authenticating...")
            self.auth._reauth()
            headers.update(self.auth.get_session_headers())
            req_kwargs["headers"] = headers
            response = self.client.session.request(method, url, **req_kwargs)

        if not response.ok:
            try:
                error_data = response.json()
            except (json.JSONDecodeError, ValueError):
                error_data = {"raw": response.text}
            error_msg = str(error_data)
            if isinstance(error_data, dict):
                value = error_data.get("value", error_data)
                messages = value.get("messages", []) if isinstance(value, dict) else []
                if messages:
                    error_msg = "; ".join(m.get("default_message", str(m)) for m in messages)
            raise VCFException(
                message=error_msg,
                status_code=response.status_code,
                response_body=response.text,
            )

        return self._handle_response(response)

    def get(self, endpoint: str, **kwargs) -> Any:
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, data: Any = None, **kwargs) -> Any:
        return self._request("POST", endpoint, data=data, **kwargs)

    def put(self, endpoint: str, data: Any = None, **kwargs) -> Any:
        return self._request("PUT", endpoint, data=data, **kwargs)

    def patch(self, endpoint: str, data: Any = None, **kwargs) -> Any:
        return self._request("PATCH", endpoint, data=data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Any:
        return self._request("DELETE", endpoint, **kwargs)

    def close(self):
        """Logout and close."""
        self.auth.close()
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

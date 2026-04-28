"""Session-based authentication for vCenter REST API."""

import logging
from typing import Optional

from vcf_sdk.base import BaseClient
from vcf_sdk.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class VCenterAuth:
    """Handle vCenter REST API session authentication.

    vCenter uses POST /api/session with Basic auth to get a session token.
    Subsequent requests use the vmware-api-session-id header.
    """

    SESSION_HEADER = "vmware-api-session-id"

    def __init__(self, hostname: str, verify_ssl: bool = False, timeout: int = 30):
        self.hostname = hostname
        self.client = BaseClient(hostname, verify_ssl=verify_ssl, timeout=timeout)
        self._session_id: Optional[str] = None
        self._username: Optional[str] = None
        self._password: Optional[str] = None

    def login(self, username: str, password: str) -> str:
        """
        Create a vCenter session.

        Args:
            username: vCenter username (e.g., administrator@vsphere.local)
            password: vCenter password

        Returns:
            Session token

        Raises:
            AuthenticationError: If login fails
        """
        self._username = username
        self._password = password
        try:
            response = self.client.session.request(
                "POST",
                f"https://{self.hostname}/api/session",
                headers={"Content-Type": "application/json"},
                auth=(username, password),
                verify=self.client.verify_ssl,
                timeout=self.client.timeout,
            )
            if not response.ok:
                raise AuthenticationError(
                    f"vCenter login failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            # Response is a bare JSON string (quoted)
            self._session_id = response.json()
            logger.debug(f"Authenticated to vCenter {self.hostname}")
            return self._session_id
        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(f"vCenter login failed: {str(e)}")

    def _reauth(self) -> None:
        """Re-authenticate using stored credentials."""
        if self._username and self._password:
            self.login(self._username, self._password)
        else:
            raise AuthenticationError("No credentials available for re-authentication")

    def get_session_headers(self) -> dict:
        """Get session headers for authenticated requests."""
        if not self._session_id:
            raise AuthenticationError("Not authenticated. Call login() first.")
        return {self.SESSION_HEADER: self._session_id}

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    def logout(self) -> None:
        """Destroy the vCenter session."""
        if self._session_id:
            try:
                self.client.session.request(
                    "DELETE",
                    f"https://{self.hostname}/api/session",
                    headers={self.SESSION_HEADER: self._session_id},
                    verify=self.client.verify_ssl,
                    timeout=self.client.timeout,
                )
            except Exception:
                pass
            self._session_id = None

    def close(self):
        """Logout and close."""
        self.logout()
        self.client.close()

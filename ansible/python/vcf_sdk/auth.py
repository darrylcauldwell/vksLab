"""Authentication handling for SDDC Manager API."""

import base64
import json
import logging
import time
from typing import Optional

from vcf_sdk.base import BaseClient
from vcf_sdk.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class SDDCAuth(BaseClient):
    """Handle SDDC Manager authentication with automatic token refresh."""

    TOKEN_REFRESH_THRESHOLD = 120  # Refresh when < 2 minutes remain

    def __init__(self, hostname: str, verify_ssl: bool = False, timeout: int = 30):
        super().__init__(hostname, verify_ssl=verify_ssl, timeout=timeout)
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    def get_token(self, username: str, password: str) -> str:
        """
        Authenticate and get bearer token.

        Args:
            username: SDDC Manager username
            password: SDDC Manager password

        Returns:
            Bearer token for API requests

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            response = self.post(
                "/v1/tokens",
                data={"username": username, "password": password},
            )
            self._access_token = response.get("accessToken")
            refresh = response.get("refreshToken", {})
            self._refresh_token = refresh.get("id") if isinstance(refresh, dict) else refresh
            logger.debug(f"Authenticated to SDDC Manager {self.hostname}")
            return self._access_token
        except Exception as e:
            raise AuthenticationError(f"Failed to authenticate: {str(e)}")

    def _decode_jwt_expiry(self, token: str) -> float:
        """Decode JWT and return expiry timestamp."""
        try:
            payload = token.split(".")[1]
            # Pad base64 to multiple of 4
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding
            decoded = json.loads(base64.urlsafe_b64decode(payload))
            return float(decoded.get("exp", 0))
        except (IndexError, ValueError, json.JSONDecodeError):
            return 0

    def _is_token_expiring(self) -> bool:
        """Check if access token is expiring within threshold."""
        if not self._access_token:
            return True
        expiry = self._decode_jwt_expiry(self._access_token)
        remaining = expiry - time.time()
        return remaining < self.TOKEN_REFRESH_THRESHOLD

    def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            raise AuthenticationError("No refresh token available. Call get_token() first.")
        try:
            url = f"https://{self.hostname}/v1/tokens/access-token/refresh"
            response = self.session.request(
                "PATCH",
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(self._refresh_token),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            if response.ok:
                self._access_token = response.text.strip().strip('"')
                logger.debug("Access token refreshed successfully")
            else:
                raise AuthenticationError(f"Token refresh failed: HTTP {response.status_code}")
        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(f"Token refresh failed: {str(e)}")

    def _ensure_token(self) -> None:
        """Ensure we have a valid, non-expiring token. Auto-refreshes if needed."""
        if not self._access_token:
            raise AuthenticationError("Not authenticated. Call get_token() first.")
        if self._is_token_expiring():
            logger.debug("Access token expiring soon, refreshing...")
            self._refresh_access_token()

    @property
    def token(self) -> Optional[str]:
        """Get current bearer token."""
        return self._access_token

    def get_auth_headers(self) -> dict:
        """Get authorization headers, auto-refreshing token if needed."""
        self._ensure_token()
        return {"Authorization": f"Bearer {self._access_token}"}

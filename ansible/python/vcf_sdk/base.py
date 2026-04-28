"""Base HTTP client for VCF APIs."""

import json
import logging
from typing import Any, Dict
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from vcf_sdk.exceptions import VCFException

logger = logging.getLogger(__name__)


class BaseClient:
    """Base HTTP client for VCF API communication."""

    def __init__(
        self,
        hostname: str,
        verify_ssl: bool = False,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize base client.

        Args:
            hostname: FQDN or IP of the API endpoint
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            max_retries: Number of retries for failed requests
        """
        self.hostname = hostname
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = self._create_session(max_retries)

    def _create_session(self, max_retries: int) -> requests.Session:
        """Create requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse response and handle errors.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON response

        Raises:
            VCFException: If response indicates an error
        """
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw": response.text}

        if not response.ok:
            # Parse error details from SDDC Manager response
            error_msg = self._extract_error_message(data)
            raise VCFException(
                message=error_msg,
                status_code=response.status_code,
                response_body=response.text,
            )

        return data

    def _extract_error_message(self, response_data: Dict[str, Any]) -> str:
        """Extract user-friendly error message from API response."""
        messages = []

        # Main error message
        if isinstance(response_data, dict):
            if response_data.get("message"):
                messages.append(response_data["message"])

            # Remediation message
            if response_data.get("remediationMessage"):
                messages.append(f"Remediation: {response_data['remediationMessage']}")

            # Nested errors
            for nested in response_data.get("nestedErrors", []):
                if nested.get("message"):
                    messages.append(f"  • {nested['message']}")

        return " | ".join(messages) if messages else str(response_data)

    def request(
        self,
        method: str,
        endpoint: str,
        headers: Dict[str, str] = None,
        data: Dict[str, Any] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (relative path)
            headers: HTTP headers
            data: Request body (will be JSON-encoded)
            **kwargs: Additional arguments for requests.request()

        Returns:
            Parsed JSON response
        """
        url = urljoin(f"https://{self.hostname}/", endpoint.lstrip("/"))
        req_headers = {"Content-Type": "application/json", **(headers or {})}

        if data:
            kwargs["data"] = json.dumps(data)

        logger.debug(f"{method} {url}")
        response = self.session.request(
            method,
            url,
            headers=req_headers,
            verify=self.verify_ssl,
            timeout=self.timeout,
            **kwargs,
        )

        return self._handle_response(response)

    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET request."""
        return self.request("GET", endpoint, **kwargs)

    def post(
        self,
        endpoint: str,
        data: Dict[str, Any] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """POST request."""
        return self.request("POST", endpoint, data=data, **kwargs)

    def put(
        self,
        endpoint: str,
        data: Dict[str, Any] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """PUT request."""
        return self.request("PUT", endpoint, data=data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request."""
        return self.request("DELETE", endpoint, **kwargs)

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

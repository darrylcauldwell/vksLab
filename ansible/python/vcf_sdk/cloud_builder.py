"""Cloud Builder API client for VCF SDDC bringup."""

import logging
from typing import Any, Dict, List, Optional

from vcf_sdk.base import BaseClient
from vcf_sdk.exceptions import ValidationError, TimeoutError

import time

logger = logging.getLogger(__name__)


class CloudBuilder:
    """
    Cloud Builder API client.

    Separate from SDDC Manager — uses Basic auth against the Cloud Builder appliance
    for initial SDDC bringup and validation.
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
        self.client = BaseClient(hostname, verify_ssl=verify_ssl, timeout=timeout)
        self._auth = (username, password)

        # Validate connectivity
        logger.debug(f"Connecting to Cloud Builder {hostname}")

    def _request(self, method: str, endpoint: str, data: Any = None, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Cloud Builder API."""
        return self.client.request(method, endpoint, data=data, auth=self._auth, **kwargs)

    def _get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._request("GET", endpoint, **kwargs)

    def _post(self, endpoint: str, data: Any = None, **kwargs) -> Dict[str, Any]:
        return self._request("POST", endpoint, data=data, **kwargs)

    def _patch(self, endpoint: str, data: Any = None, **kwargs) -> Dict[str, Any]:
        return self._request("PATCH", endpoint, data=data, **kwargs)

    def _delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._request("DELETE", endpoint, **kwargs)

    # Depot Configuration

    def get_depot(self) -> Dict[str, Any]:
        """Get current depot configuration."""
        return self._get("/v1/sddcs/depot")

    def set_depot(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure the VCF offline depot.

        Args:
            spec: Depot configuration with offlineAccount and depotConfiguration

        Returns:
            Depot configuration response
        """
        response = self.client.request(
            "PUT", "/v1/sddcs/depot", data=spec, auth=self._auth
        )
        logger.info("Depot configuration updated")
        return response

    # SDDC Bringup

    def list_sddcs(self) -> List[Dict[str, Any]]:
        """List all SDDC deployment tasks."""
        response = self._get("/v1/sddcs")
        return response.get("elements", [])

    def get_sddc(self, sddc_id: str) -> Dict[str, Any]:
        """Get SDDC deployment task by ID."""
        return self._get(f"/v1/sddcs/{sddc_id}")

    def start_bringup(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start SDDC bringup.

        Args:
            spec: SDDC bringup specification (JSON)

        Returns:
            Bringup task response
        """
        response = self._post("/v1/sddcs", data=spec)
        logger.info(f"Started SDDC bringup, task ID: {response.get('id')}")
        return response

    def retry_bringup(self, sddc_id: str, spec: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Retry a failed SDDC bringup.

        Args:
            sddc_id: SDDC deployment task ID
            spec: Optional updated spec
        """
        return self._patch(f"/v1/sddcs/{sddc_id}", data=spec)

    # SDDC Validations

    def list_validations(self) -> List[Dict[str, Any]]:
        """List all SDDC validation tasks."""
        response = self._get("/v1/sddcs/validations")
        return response.get("elements", [])

    def get_validation(self, validation_id: str) -> Dict[str, Any]:
        """Get SDDC validation status."""
        return self._get(f"/v1/sddcs/validations/{validation_id}")

    def start_validation(
        self, spec: Dict[str, Any], validation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start SDDC validation.

        Args:
            spec: SDDC spec to validate
            validation_type: Optional specific validation to run, e.g.:
                JSON_SPEC_VALIDATION, LICENSE_KEY_VALIDATION, TIME_SYNC_VALIDATION,
                NETWORK_IP_POOLS_VALIDATION, NETWORK_CONFIG_VALIDATION,
                MANAGEMENT_NETWORKS_VALIDATION, ESXI_VERSION_VALIDATION,
                ESXI_HOST_READINESS_VALIDATION, PASSWORDS_VALIDATION,
                HOST_IP_DNS_VALIDATION, CLOUDBUILDER_READY_VALIDATION,
                VSAN_AVAILABILITY_VALIDATION, NSXT_NETWORKS_VALIDATION,
                AVN_NETWORKS_VALIDATION, SECURE_PLATFORM_AUDIT
        """
        endpoint = "/v1/sddcs/validations"
        if validation_type:
            endpoint += f"?name={validation_type}"
        response = self._post(endpoint, data=spec)
        logger.info(f"Started SDDC validation, ID: {response.get('id')}")
        return response

    def stop_validation(self, validation_id: str) -> None:
        """Stop a running validation."""
        self._delete(f"/v1/sddcs/validations/{validation_id}")

    def retry_validation(self, validation_id: str) -> Dict[str, Any]:
        """Retry a failed validation."""
        return self._patch(f"/v1/sddcs/validations/{validation_id}")

    def wait_for_validation(
        self, validation_id: str, timeout: int = 600, poll_interval: int = 10
    ) -> Dict[str, Any]:
        """
        Wait for validation to complete.

        Returns:
            Final validation result

        Raises:
            ValidationError: If validation fails
            TimeoutError: If timeout exceeded
        """
        start_time = time.time()
        while True:
            result = self.get_validation(validation_id)
            execution_status = result.get("executionStatus")

            if execution_status == "COMPLETED":
                result_status = result.get("resultStatus")
                if result_status != "SUCCEEDED":
                    raise ValidationError(
                        message=f"SDDC validation failed: {result_status}",
                        response_body=str(result),
                    )
                return result

            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Validation {validation_id} timed out after {timeout}s"
                )

            logger.debug(f"Validation {validation_id}: {execution_status}, elapsed: {elapsed:.0f}s")
            time.sleep(poll_interval)

    def close(self):
        """Close connection."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

"""Base manager with shared patterns."""

import logging
import time
from typing import Any, Dict

from vcf_sdk.auth import SDDCAuth
from vcf_sdk.base import BaseClient
from vcf_sdk.exceptions import ValidationError, TimeoutError

logger = logging.getLogger(__name__)


class BaseManager:
    """Base class for all SDDC Manager resource managers."""

    def __init__(self, client: BaseClient, auth: SDDCAuth):
        self.client = client
        self.auth = auth

    def _get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self.client.get(endpoint, headers=self.auth.get_auth_headers(), **kwargs)

    def _post(self, endpoint: str, data=None, **kwargs) -> Dict[str, Any]:
        return self.client.post(endpoint, data=data, headers=self.auth.get_auth_headers(), **kwargs)

    def _put(self, endpoint: str, data=None, **kwargs) -> Dict[str, Any]:
        return self.client.put(endpoint, data=data, headers=self.auth.get_auth_headers(), **kwargs)

    def _patch(self, endpoint: str, data=None, **kwargs) -> Dict[str, Any]:
        return self.client.request(
            "PATCH", endpoint, data=data, headers=self.auth.get_auth_headers(), **kwargs
        )

    def _delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self.client.delete(endpoint, headers=self.auth.get_auth_headers(), **kwargs)

    def _validate_and_wait(
        self,
        validation_endpoint: str,
        spec: Dict[str, Any],
        poll_endpoint_template: str = None,
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> Dict[str, Any]:
        """
        Validate-then-execute pattern from PowerVCF.

        1. POST spec to validation endpoint
        2. Poll until validation completes
        3. Return validation result (caller checks success before proceeding)
        """
        response = self._post(validation_endpoint, data=spec)
        validation_id = response.get("id")

        if not validation_id:
            return response

        poll_endpoint = (
            poll_endpoint_template.format(id=validation_id)
            if poll_endpoint_template
            else f"{validation_endpoint}/{validation_id}"
        )

        start_time = time.time()
        while True:
            result = self._get(poll_endpoint)
            execution_status = result.get("executionStatus")

            if execution_status == "COMPLETED":
                result_status = result.get("resultStatus")
                if result_status != "SUCCEEDED":
                    raise ValidationError(
                        message=f"Validation failed: {result.get('validationChecks', [])}",
                        status_code=None,
                        response_body=str(result),
                    )
                return result

            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Validation {validation_id} timed out after {timeout}s")

            time.sleep(poll_interval)

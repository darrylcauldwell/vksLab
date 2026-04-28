"""OVF deployment management for vCenter REST API."""

from typing import Any, Dict

from vcf_sdk.models.vcenter import OVFDeployResult
from vcf_sdk.vcenter.base import VCBaseManager


class OVFManager(VCBaseManager):
    """Deploy OVF/OVA from content library."""

    def get_deploy_options(self, item_id: str, target: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get OVF deployment options (network/storage sections, properties).

        Args:
            item_id: Content library OVF item ID
            target: Deployment target {"resource_pool_id": "..."}
        """
        return self._post(
            f"/vcenter/ovf/library-item/{item_id}?action=filter",
            data={"target": target},
        )

    def deploy(self, item_id: str, spec: Dict[str, Any]) -> OVFDeployResult:
        """
        Deploy an OVF from content library.

        Args:
            item_id: Content library OVF item ID
            spec: Deployment spec with target and deployment_spec
        """
        response = self._post(
            f"/vcenter/ovf/library-item/{item_id}?action=deploy",
            data=spec,
        )
        return OVFDeployResult(**response)

"""Advanced security management (context profiles, IDS/IPS, firewall exclude) for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx.advanced_security import (
    ContextProfile, L7AccessProfile,
    IntrusionServicePolicy, IntrusionServiceProfile,
    IntrusionServiceGatewayPolicy, IDSSettings, IDSSignatureVersion,
)
from vcf_sdk.models.nsx.security import SecurityPolicy, GatewayPolicy
from vcf_sdk.nsx.base import NSXBaseManager

DOMAIN = "default"


class ContextProfileManager(NSXBaseManager):
    """Manage L7 context profiles and custom attributes."""

    def list(self) -> List[ContextProfile]:
        return self._list("/infra/context-profiles", ContextProfile)

    def get(self, profile_id: str) -> ContextProfile:
        return self._get(f"/infra/context-profiles/{profile_id}", ContextProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/context-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/context-profiles/{profile_id}")

    # Custom attributes

    def list_custom_attributes(self) -> List[Dict[str, Any]]:
        response = self._raw_get("/infra/context-profiles/custom-attributes")
        return response.get("results", [])

    def create_or_update_custom_attribute(
        self, attr_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", attr_id)
        return self._create_or_update(
            f"/infra/context-profiles/custom-attributes/{attr_id}", spec
        )


class L7AccessProfileManager(NSXBaseManager):
    """Manage L7 access profiles."""

    def list(self) -> List[L7AccessProfile]:
        return self._list("/infra/l7-access-profiles", L7AccessProfile)

    def get(self, profile_id: str) -> L7AccessProfile:
        return self._get(f"/infra/l7-access-profiles/{profile_id}", L7AccessProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/l7-access-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/l7-access-profiles/{profile_id}")


class IDSIPSManager(NSXBaseManager):
    """Manage IDS/IPS policies, profiles, gateway policies, and settings."""

    # Distributed IDS policies

    def list_policies(self) -> List[IntrusionServicePolicy]:
        return self._list(
            f"/infra/domains/{DOMAIN}/intrusion-service-policies", IntrusionServicePolicy
        )

    def get_policy(self, policy_id: str) -> IntrusionServicePolicy:
        return self._get(
            f"/infra/domains/{DOMAIN}/intrusion-service-policies/{policy_id}",
            IntrusionServicePolicy,
        )

    def create_or_update_policy(
        self, policy_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", policy_id)
        return self._create_or_update(
            f"/infra/domains/{DOMAIN}/intrusion-service-policies/{policy_id}", spec
        )

    def delete_policy(self, policy_id: str) -> None:
        self._delete(f"/infra/domains/{DOMAIN}/intrusion-service-policies/{policy_id}")

    # IDS profiles

    def list_profiles(self) -> List[IntrusionServiceProfile]:
        return self._list("/infra/settings/firewall/idfw/ids-profiles", IntrusionServiceProfile)

    def get_profile(self, profile_id: str) -> IntrusionServiceProfile:
        return self._get(
            f"/infra/settings/firewall/idfw/ids-profiles/{profile_id}",
            IntrusionServiceProfile,
        )

    def create_or_update_profile(
        self, profile_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(
            f"/infra/settings/firewall/idfw/ids-profiles/{profile_id}", spec
        )

    # Gateway IDS policies

    def list_gateway_policies(self) -> List[IntrusionServiceGatewayPolicy]:
        return self._list(
            f"/infra/domains/{DOMAIN}/intrusion-service-gateway-policies",
            IntrusionServiceGatewayPolicy,
        )

    def get_gateway_policy(self, policy_id: str) -> IntrusionServiceGatewayPolicy:
        return self._get(
            f"/infra/domains/{DOMAIN}/intrusion-service-gateway-policies/{policy_id}",
            IntrusionServiceGatewayPolicy,
        )

    def create_or_update_gateway_policy(
        self, policy_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", policy_id)
        return self._create_or_update(
            f"/infra/domains/{DOMAIN}/intrusion-service-gateway-policies/{policy_id}", spec
        )

    # Global settings

    def get_settings(self) -> IDSSettings:
        return self._get("/infra/settings/firewall/security/intrusion-services", IDSSettings)

    def update_settings(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        return self._create_or_update(
            "/infra/settings/firewall/security/intrusion-services", spec
        )

    # Signature versions

    def list_signature_versions(self) -> List[IDSSignatureVersion]:
        return self._list(
            "/infra/settings/firewall/security/intrusion-services/signature-versions",
            IDSSignatureVersion,
        )


class PredefinedSecurityPolicyManager(NSXBaseManager):
    """Manage predefined (system-created) security and gateway policies."""

    def list_security_policies(self) -> List[SecurityPolicy]:
        return self._list(
            f"/infra/domains/{DOMAIN}/security-policies", SecurityPolicy
        )

    def get_predefined_security_policy(self, policy_id: str) -> SecurityPolicy:
        return self._get(
            f"/infra/domains/{DOMAIN}/security-policies/{policy_id}", SecurityPolicy
        )

    def list_gateway_policies(self) -> List[GatewayPolicy]:
        return self._list(
            f"/infra/domains/{DOMAIN}/gateway-policies", GatewayPolicy
        )

    def get_predefined_gateway_policy(self, policy_id: str) -> GatewayPolicy:
        return self._get(
            f"/infra/domains/{DOMAIN}/gateway-policies/{policy_id}", GatewayPolicy
        )


class FirewallExcludeListManager(NSXBaseManager):
    """Manage the distributed firewall exclude list."""

    def get(self) -> Dict[str, Any]:
        """Get the firewall exclude list."""
        return self._raw_get("/infra/settings/firewall/security/exclude-list")

    def update(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update the firewall exclude list (add/remove members)."""
        return self._create_or_update(
            "/infra/settings/firewall/security/exclude-list", spec
        )


class ClusterSecurityConfigManager(NSXBaseManager):
    """Manage cluster-level security configuration."""

    def get(self, cluster_id: str) -> Dict[str, Any]:
        return self._raw_get(f"/infra/sites/default/enforcement-points/default/cluster-security-configs/{cluster_id}")

    def update(self, cluster_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", cluster_id)
        return self._create_or_update(
            f"/infra/sites/default/enforcement-points/default/cluster-security-configs/{cluster_id}",
            spec,
        )

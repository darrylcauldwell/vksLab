"""Infrastructure profile management for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx.profiles import (
    IPDiscoveryProfile, MACDiscoveryProfile, SpoofGuardProfile,
    SegmentSecurityProfile, QoSProfile, GatewayQoSProfile,
    FloodProtectionProfile, FloodProtectionProfileBinding,
)
from vcf_sdk.nsx.base import NSXBaseManager


class IPDiscoveryProfileManager(NSXBaseManager):
    """Manage IP discovery profiles."""

    def list(self) -> List[IPDiscoveryProfile]:
        return self._list("/infra/ip-discovery-profiles", IPDiscoveryProfile)

    def get(self, profile_id: str) -> IPDiscoveryProfile:
        return self._get(f"/infra/ip-discovery-profiles/{profile_id}", IPDiscoveryProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/ip-discovery-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/ip-discovery-profiles/{profile_id}")


class MACDiscoveryProfileManager(NSXBaseManager):
    """Manage MAC discovery profiles."""

    def list(self) -> List[MACDiscoveryProfile]:
        return self._list("/infra/mac-discovery-profiles", MACDiscoveryProfile)

    def get(self, profile_id: str) -> MACDiscoveryProfile:
        return self._get(f"/infra/mac-discovery-profiles/{profile_id}", MACDiscoveryProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/mac-discovery-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/mac-discovery-profiles/{profile_id}")


class SpoofGuardProfileManager(NSXBaseManager):
    """Manage spoof guard profiles."""

    def list(self) -> List[SpoofGuardProfile]:
        return self._list("/infra/spoofguard-profiles", SpoofGuardProfile)

    def get(self, profile_id: str) -> SpoofGuardProfile:
        return self._get(f"/infra/spoofguard-profiles/{profile_id}", SpoofGuardProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/spoofguard-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/spoofguard-profiles/{profile_id}")


class SegmentSecurityProfileManager(NSXBaseManager):
    """Manage segment security profiles."""

    def list(self) -> List[SegmentSecurityProfile]:
        return self._list("/infra/segment-security-profiles", SegmentSecurityProfile)

    def get(self, profile_id: str) -> SegmentSecurityProfile:
        return self._get(f"/infra/segment-security-profiles/{profile_id}", SegmentSecurityProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/segment-security-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/segment-security-profiles/{profile_id}")


class QoSProfileManager(NSXBaseManager):
    """Manage QoS profiles."""

    def list(self) -> List[QoSProfile]:
        return self._list("/infra/qos-profiles", QoSProfile)

    def get(self, profile_id: str) -> QoSProfile:
        return self._get(f"/infra/qos-profiles/{profile_id}", QoSProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/qos-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/qos-profiles/{profile_id}")


class GatewayQoSProfileManager(NSXBaseManager):
    """Manage gateway QoS profiles."""

    def list(self) -> List[GatewayQoSProfile]:
        return self._list("/infra/gateway-qos-profiles", GatewayQoSProfile)

    def get(self, profile_id: str) -> GatewayQoSProfile:
        return self._get(f"/infra/gateway-qos-profiles/{profile_id}", GatewayQoSProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/gateway-qos-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/gateway-qos-profiles/{profile_id}")


class GatewayFloodProtectionProfileManager(NSXBaseManager):
    """Manage gateway flood protection profiles and bindings."""

    def list(self) -> List[FloodProtectionProfile]:
        return self._list("/infra/flood-protection-profiles", FloodProtectionProfile)

    def get(self, profile_id: str) -> FloodProtectionProfile:
        return self._get(f"/infra/flood-protection-profiles/{profile_id}", FloodProtectionProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/flood-protection-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/flood-protection-profiles/{profile_id}")

    # Bindings (on gateways)

    def list_tier0_bindings(self, tier0_id: str) -> List[FloodProtectionProfileBinding]:
        return self._list(
            f"/infra/tier-0s/{tier0_id}/flood-protection-profile-bindings",
            FloodProtectionProfileBinding,
        )

    def set_tier0_binding(
        self, tier0_id: str, binding_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", binding_id)
        return self._create_or_update(
            f"/infra/tier-0s/{tier0_id}/flood-protection-profile-bindings/{binding_id}", spec
        )

    def list_tier1_bindings(self, tier1_id: str) -> List[FloodProtectionProfileBinding]:
        return self._list(
            f"/infra/tier-1s/{tier1_id}/flood-protection-profile-bindings",
            FloodProtectionProfileBinding,
        )

    def set_tier1_binding(
        self, tier1_id: str, binding_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", binding_id)
        return self._create_or_update(
            f"/infra/tier-1s/{tier1_id}/flood-protection-profile-bindings/{binding_id}", spec
        )

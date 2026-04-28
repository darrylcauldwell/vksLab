"""VPN management (IPSec + L2) for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx.vpn import (
    IPSecVPNService, IPSecVPNSession, IPSecVPNLocalEndpoint,
    IPSecVPNIKEProfile, IPSecVPNTunnelProfile, IPSecVPNDPDProfile,
    L2VPNService, L2VPNSession,
)
from vcf_sdk.nsx.base import NSXBaseManager


class IPSecVPNManager(NSXBaseManager):
    """Manage IPSec VPN services, sessions, endpoints, and profiles."""

    def _svc_path(self, gw_type: str, gw_id: str) -> str:
        return f"/infra/{gw_type}/{gw_id}/ipsec-vpn-services"

    # Services (on Tier-0 or Tier-1)

    def list_services(self, gw_type: str, gw_id: str) -> List[IPSecVPNService]:
        return self._list(self._svc_path(gw_type, gw_id), IPSecVPNService)

    def get_service(self, gw_type: str, gw_id: str, svc_id: str) -> IPSecVPNService:
        return self._get(f"{self._svc_path(gw_type, gw_id)}/{svc_id}", IPSecVPNService)

    def create_or_update_service(
        self, gw_type: str, gw_id: str, svc_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", svc_id)
        return self._create_or_update(f"{self._svc_path(gw_type, gw_id)}/{svc_id}", spec)

    def delete_service(self, gw_type: str, gw_id: str, svc_id: str) -> None:
        self._delete(f"{self._svc_path(gw_type, gw_id)}/{svc_id}")

    # Sessions

    def list_sessions(
        self, gw_type: str, gw_id: str, svc_id: str
    ) -> List[IPSecVPNSession]:
        return self._list(
            f"{self._svc_path(gw_type, gw_id)}/{svc_id}/sessions", IPSecVPNSession
        )

    def get_session(
        self, gw_type: str, gw_id: str, svc_id: str, session_id: str
    ) -> IPSecVPNSession:
        return self._get(
            f"{self._svc_path(gw_type, gw_id)}/{svc_id}/sessions/{session_id}",
            IPSecVPNSession,
        )

    def create_or_update_session(
        self, gw_type: str, gw_id: str, svc_id: str, session_id: str,
        spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", session_id)
        return self._create_or_update(
            f"{self._svc_path(gw_type, gw_id)}/{svc_id}/sessions/{session_id}", spec
        )

    def delete_session(
        self, gw_type: str, gw_id: str, svc_id: str, session_id: str
    ) -> None:
        self._delete(
            f"{self._svc_path(gw_type, gw_id)}/{svc_id}/sessions/{session_id}"
        )

    # Local Endpoints

    def list_local_endpoints(
        self, gw_type: str, gw_id: str, svc_id: str
    ) -> List[IPSecVPNLocalEndpoint]:
        return self._list(
            f"{self._svc_path(gw_type, gw_id)}/{svc_id}/local-endpoints",
            IPSecVPNLocalEndpoint,
        )

    def get_local_endpoint(
        self, gw_type: str, gw_id: str, svc_id: str, ep_id: str
    ) -> IPSecVPNLocalEndpoint:
        return self._get(
            f"{self._svc_path(gw_type, gw_id)}/{svc_id}/local-endpoints/{ep_id}",
            IPSecVPNLocalEndpoint,
        )

    def create_or_update_local_endpoint(
        self, gw_type: str, gw_id: str, svc_id: str, ep_id: str,
        spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", ep_id)
        return self._create_or_update(
            f"{self._svc_path(gw_type, gw_id)}/{svc_id}/local-endpoints/{ep_id}", spec
        )

    def delete_local_endpoint(
        self, gw_type: str, gw_id: str, svc_id: str, ep_id: str
    ) -> None:
        self._delete(
            f"{self._svc_path(gw_type, gw_id)}/{svc_id}/local-endpoints/{ep_id}"
        )

    # IKE Profiles (global)

    def list_ike_profiles(self) -> List[IPSecVPNIKEProfile]:
        return self._list("/infra/ipsec-vpn-ike-profiles", IPSecVPNIKEProfile)

    def get_ike_profile(self, profile_id: str) -> IPSecVPNIKEProfile:
        return self._get(f"/infra/ipsec-vpn-ike-profiles/{profile_id}", IPSecVPNIKEProfile)

    def create_or_update_ike_profile(
        self, profile_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/ipsec-vpn-ike-profiles/{profile_id}", spec)

    def delete_ike_profile(self, profile_id: str) -> None:
        self._delete(f"/infra/ipsec-vpn-ike-profiles/{profile_id}")

    # Tunnel Profiles (global)

    def list_tunnel_profiles(self) -> List[IPSecVPNTunnelProfile]:
        return self._list("/infra/ipsec-vpn-tunnel-profiles", IPSecVPNTunnelProfile)

    def get_tunnel_profile(self, profile_id: str) -> IPSecVPNTunnelProfile:
        return self._get(
            f"/infra/ipsec-vpn-tunnel-profiles/{profile_id}", IPSecVPNTunnelProfile
        )

    def create_or_update_tunnel_profile(
        self, profile_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/ipsec-vpn-tunnel-profiles/{profile_id}", spec)

    def delete_tunnel_profile(self, profile_id: str) -> None:
        self._delete(f"/infra/ipsec-vpn-tunnel-profiles/{profile_id}")

    # DPD Profiles (global)

    def list_dpd_profiles(self) -> List[IPSecVPNDPDProfile]:
        return self._list("/infra/ipsec-vpn-dpd-profiles", IPSecVPNDPDProfile)

    def get_dpd_profile(self, profile_id: str) -> IPSecVPNDPDProfile:
        return self._get(f"/infra/ipsec-vpn-dpd-profiles/{profile_id}", IPSecVPNDPDProfile)

    def create_or_update_dpd_profile(
        self, profile_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/ipsec-vpn-dpd-profiles/{profile_id}", spec)

    def delete_dpd_profile(self, profile_id: str) -> None:
        self._delete(f"/infra/ipsec-vpn-dpd-profiles/{profile_id}")


class L2VPNManager(NSXBaseManager):
    """Manage L2 VPN services and sessions."""

    def _svc_path(self, gw_type: str, gw_id: str) -> str:
        return f"/infra/{gw_type}/{gw_id}/l2vpn-services"

    # Services

    def list_services(self, gw_type: str, gw_id: str) -> List[L2VPNService]:
        return self._list(self._svc_path(gw_type, gw_id), L2VPNService)

    def get_service(self, gw_type: str, gw_id: str, svc_id: str) -> L2VPNService:
        return self._get(f"{self._svc_path(gw_type, gw_id)}/{svc_id}", L2VPNService)

    def create_or_update_service(
        self, gw_type: str, gw_id: str, svc_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", svc_id)
        return self._create_or_update(f"{self._svc_path(gw_type, gw_id)}/{svc_id}", spec)

    def delete_service(self, gw_type: str, gw_id: str, svc_id: str) -> None:
        self._delete(f"{self._svc_path(gw_type, gw_id)}/{svc_id}")

    # Sessions

    def list_sessions(
        self, gw_type: str, gw_id: str, svc_id: str
    ) -> List[L2VPNSession]:
        return self._list(
            f"{self._svc_path(gw_type, gw_id)}/{svc_id}/sessions", L2VPNSession
        )

    def get_session(
        self, gw_type: str, gw_id: str, svc_id: str, session_id: str
    ) -> L2VPNSession:
        return self._get(
            f"{self._svc_path(gw_type, gw_id)}/{svc_id}/sessions/{session_id}", L2VPNSession
        )

    def create_or_update_session(
        self, gw_type: str, gw_id: str, svc_id: str, session_id: str,
        spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", session_id)
        return self._create_or_update(
            f"{self._svc_path(gw_type, gw_id)}/{svc_id}/sessions/{session_id}", spec
        )

    def delete_session(
        self, gw_type: str, gw_id: str, svc_id: str, session_id: str
    ) -> None:
        self._delete(
            f"{self._svc_path(gw_type, gw_id)}/{svc_id}/sessions/{session_id}"
        )

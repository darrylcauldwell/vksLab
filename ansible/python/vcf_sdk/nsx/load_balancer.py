"""Load Balancer management for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx.load_balancer import (
    LBService, LBVirtualServer, LBPool,
    LBMonitorProfile, LBAppProfile, LBPersistenceProfile, LBSSLProfile,
)
from vcf_sdk.nsx.base import NSXBaseManager


class LBServiceManager(NSXBaseManager):
    """Manage LB services."""

    def list(self) -> List[LBService]:
        return self._list("/infra/lb-services", LBService)

    def get(self, service_id: str) -> LBService:
        return self._get(f"/infra/lb-services/{service_id}", LBService)

    def create_or_update(self, service_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", service_id)
        return self._create_or_update(f"/infra/lb-services/{service_id}", spec)

    def delete(self, service_id: str) -> None:
        self._delete(f"/infra/lb-services/{service_id}")


class LBVirtualServerManager(NSXBaseManager):
    """Manage LB virtual servers."""

    def list(self) -> List[LBVirtualServer]:
        return self._list("/infra/lb-virtual-servers", LBVirtualServer)

    def get(self, vs_id: str) -> LBVirtualServer:
        return self._get(f"/infra/lb-virtual-servers/{vs_id}", LBVirtualServer)

    def create_or_update(self, vs_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", vs_id)
        return self._create_or_update(f"/infra/lb-virtual-servers/{vs_id}", spec)

    def delete(self, vs_id: str) -> None:
        self._delete(f"/infra/lb-virtual-servers/{vs_id}")


class LBPoolManager(NSXBaseManager):
    """Manage LB server pools."""

    def list(self) -> List[LBPool]:
        return self._list("/infra/lb-pools", LBPool)

    def get(self, pool_id: str) -> LBPool:
        return self._get(f"/infra/lb-pools/{pool_id}", LBPool)

    def create_or_update(self, pool_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", pool_id)
        return self._create_or_update(f"/infra/lb-pools/{pool_id}", spec)

    def delete(self, pool_id: str) -> None:
        self._delete(f"/infra/lb-pools/{pool_id}")


class LBMonitorProfileManager(NSXBaseManager):
    """Manage LB monitor profiles (HTTP, HTTPS, TCP, UDP, ICMP, passive)."""

    def list(self) -> List[LBMonitorProfile]:
        return self._list("/infra/lb-monitor-profiles", LBMonitorProfile)

    def get(self, profile_id: str) -> LBMonitorProfile:
        return self._get(f"/infra/lb-monitor-profiles/{profile_id}", LBMonitorProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/lb-monitor-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/lb-monitor-profiles/{profile_id}")


class LBAppProfileManager(NSXBaseManager):
    """Manage LB application profiles (HTTP, fast TCP, fast UDP)."""

    def list(self) -> List[LBAppProfile]:
        return self._list("/infra/lb-app-profiles", LBAppProfile)

    def get(self, profile_id: str) -> LBAppProfile:
        return self._get(f"/infra/lb-app-profiles/{profile_id}", LBAppProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/lb-app-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/lb-app-profiles/{profile_id}")


class LBPersistenceProfileManager(NSXBaseManager):
    """Manage LB persistence profiles (cookie, source IP, generic)."""

    def list(self) -> List[LBPersistenceProfile]:
        return self._list("/infra/lb-persistence-profiles", LBPersistenceProfile)

    def get(self, profile_id: str) -> LBPersistenceProfile:
        return self._get(f"/infra/lb-persistence-profiles/{profile_id}", LBPersistenceProfile)

    def create_or_update(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/lb-persistence-profiles/{profile_id}", spec)

    def delete(self, profile_id: str) -> None:
        self._delete(f"/infra/lb-persistence-profiles/{profile_id}")


class LBSSLProfileManager(NSXBaseManager):
    """Manage LB SSL profiles (client and server)."""

    def list_client(self) -> List[LBSSLProfile]:
        return self._list("/infra/lb-client-ssl-profiles", LBSSLProfile)

    def get_client(self, profile_id: str) -> LBSSLProfile:
        return self._get(f"/infra/lb-client-ssl-profiles/{profile_id}", LBSSLProfile)

    def create_or_update_client(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/lb-client-ssl-profiles/{profile_id}", spec)

    def delete_client(self, profile_id: str) -> None:
        self._delete(f"/infra/lb-client-ssl-profiles/{profile_id}")

    def list_server(self) -> List[LBSSLProfile]:
        return self._list("/infra/lb-server-ssl-profiles", LBSSLProfile)

    def get_server(self, profile_id: str) -> LBSSLProfile:
        return self._get(f"/infra/lb-server-ssl-profiles/{profile_id}", LBSSLProfile)

    def create_or_update_server(self, profile_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", profile_id)
        return self._create_or_update(f"/infra/lb-server-ssl-profiles/{profile_id}", spec)

    def delete_server(self, profile_id: str) -> None:
        self._delete(f"/infra/lb-server-ssl-profiles/{profile_id}")

"""Service management for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx import Service
from vcf_sdk.nsx.base import NSXBaseManager


class ServiceManager(NSXBaseManager):
    """Manage NSX-T services (L4 port definitions)."""

    def list(self) -> List[Service]:
        return self._list("/infra/services", Service)

    def get(self, service_id: str) -> Service:
        return self._get(f"/infra/services/{service_id}", Service)

    def create_or_update(self, service_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", service_id)
        return self._create_or_update(f"/infra/services/{service_id}", spec)

    def delete(self, service_id: str) -> None:
        self._delete(f"/infra/services/{service_id}")

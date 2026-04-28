"""Tier-1 gateway management for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx import Tier1Gateway, LocaleService, GatewayInterface, StaticRoute, PrefixList
from vcf_sdk.nsx.base import NSXBaseManager


class Tier1Manager(NSXBaseManager):
    """Manage NSX-T Tier-1 gateways, locale services, interfaces."""

    # Tier-1 CRUD

    def list(self) -> List[Tier1Gateway]:
        return self._list("/infra/tier-1s", Tier1Gateway)

    def get(self, tier1_id: str) -> Tier1Gateway:
        return self._get(f"/infra/tier-1s/{tier1_id}", Tier1Gateway)

    def create_or_update(self, tier1_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", tier1_id)
        return self._create_or_update(f"/infra/tier-1s/{tier1_id}", spec)

    def delete(self, tier1_id: str) -> None:
        self._delete(f"/infra/tier-1s/{tier1_id}")

    # Locale Services

    def list_locale_services(self, tier1_id: str) -> List[LocaleService]:
        return self._list(f"/infra/tier-1s/{tier1_id}/locale-services", LocaleService)

    def get_locale_service(self, tier1_id: str, ls_id: str) -> LocaleService:
        return self._get(f"/infra/tier-1s/{tier1_id}/locale-services/{ls_id}", LocaleService)

    def create_or_update_locale_service(
        self, tier1_id: str, ls_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", ls_id)
        return self._create_or_update(
            f"/infra/tier-1s/{tier1_id}/locale-services/{ls_id}", spec
        )

    def delete_locale_service(self, tier1_id: str, ls_id: str) -> None:
        self._delete(f"/infra/tier-1s/{tier1_id}/locale-services/{ls_id}")

    # Interfaces

    def list_interfaces(self, tier1_id: str, ls_id: str) -> List[GatewayInterface]:
        return self._list(
            f"/infra/tier-1s/{tier1_id}/locale-services/{ls_id}/interfaces",
            GatewayInterface,
        )

    def get_interface(self, tier1_id: str, ls_id: str, if_id: str) -> GatewayInterface:
        return self._get(
            f"/infra/tier-1s/{tier1_id}/locale-services/{ls_id}/interfaces/{if_id}",
            GatewayInterface,
        )

    def create_or_update_interface(
        self, tier1_id: str, ls_id: str, if_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", if_id)
        return self._create_or_update(
            f"/infra/tier-1s/{tier1_id}/locale-services/{ls_id}/interfaces/{if_id}", spec
        )

    def delete_interface(self, tier1_id: str, ls_id: str, if_id: str) -> None:
        self._delete(
            f"/infra/tier-1s/{tier1_id}/locale-services/{ls_id}/interfaces/{if_id}"
        )

    # Static Routes

    def list_static_routes(self, tier1_id: str) -> List[StaticRoute]:
        return self._list(f"/infra/tier-1s/{tier1_id}/static-routes", StaticRoute)

    def create_or_update_static_route(
        self, tier1_id: str, route_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", route_id)
        return self._create_or_update(
            f"/infra/tier-1s/{tier1_id}/static-routes/{route_id}", spec
        )

    def delete_static_route(self, tier1_id: str, route_id: str) -> None:
        self._delete(f"/infra/tier-1s/{tier1_id}/static-routes/{route_id}")

    # Prefix Lists

    def list_prefix_lists(self, tier1_id: str) -> List[PrefixList]:
        return self._list(f"/infra/tier-1s/{tier1_id}/prefix-lists", PrefixList)

    def get_prefix_list(self, tier1_id: str, pl_id: str) -> PrefixList:
        return self._get(f"/infra/tier-1s/{tier1_id}/prefix-lists/{pl_id}", PrefixList)

    def create_or_update_prefix_list(
        self, tier1_id: str, pl_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", pl_id)
        return self._create_or_update(f"/infra/tier-1s/{tier1_id}/prefix-lists/{pl_id}", spec)

    def delete_prefix_list(self, tier1_id: str, pl_id: str) -> None:
        self._delete(f"/infra/tier-1s/{tier1_id}/prefix-lists/{pl_id}")

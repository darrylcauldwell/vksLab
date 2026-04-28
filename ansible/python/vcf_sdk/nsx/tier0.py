"""Tier-0 gateway management for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx import (
    Tier0Gateway, LocaleService, GatewayInterface, StaticRoute, BGPConfig, BGPNeighbor,
    OSPFConfig, OSPFArea, PrefixList, CommunityList, RouteMap,
)
from vcf_sdk.nsx.base import NSXBaseManager


class Tier0Manager(NSXBaseManager):
    """Manage NSX-T Tier-0 gateways, locale services, interfaces, routing."""

    # Tier-0 CRUD

    def list(self) -> List[Tier0Gateway]:
        return self._list("/infra/tier-0s", Tier0Gateway)

    def get(self, tier0_id: str) -> Tier0Gateway:
        return self._get(f"/infra/tier-0s/{tier0_id}", Tier0Gateway)

    def create_or_update(self, tier0_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        spec.setdefault("id", tier0_id)
        return self._create_or_update(f"/infra/tier-0s/{tier0_id}", spec)

    def delete(self, tier0_id: str) -> None:
        self._delete(f"/infra/tier-0s/{tier0_id}")

    # Locale Services

    def list_locale_services(self, tier0_id: str) -> List[LocaleService]:
        return self._list(f"/infra/tier-0s/{tier0_id}/locale-services", LocaleService)

    def get_locale_service(self, tier0_id: str, ls_id: str) -> LocaleService:
        return self._get(f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}", LocaleService)

    def create_or_update_locale_service(
        self, tier0_id: str, ls_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", ls_id)
        return self._create_or_update(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}", spec
        )

    def delete_locale_service(self, tier0_id: str, ls_id: str) -> None:
        self._delete(f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}")

    # Interfaces

    def list_interfaces(self, tier0_id: str, ls_id: str) -> List[GatewayInterface]:
        return self._list(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/interfaces",
            GatewayInterface,
        )

    def get_interface(self, tier0_id: str, ls_id: str, if_id: str) -> GatewayInterface:
        return self._get(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/interfaces/{if_id}",
            GatewayInterface,
        )

    def create_or_update_interface(
        self, tier0_id: str, ls_id: str, if_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", if_id)
        return self._create_or_update(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/interfaces/{if_id}", spec
        )

    def delete_interface(self, tier0_id: str, ls_id: str, if_id: str) -> None:
        self._delete(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/interfaces/{if_id}"
        )

    # Static Routes

    def list_static_routes(self, tier0_id: str) -> List[StaticRoute]:
        return self._list(f"/infra/tier-0s/{tier0_id}/static-routes", StaticRoute)

    def get_static_route(self, tier0_id: str, route_id: str) -> StaticRoute:
        return self._get(f"/infra/tier-0s/{tier0_id}/static-routes/{route_id}", StaticRoute)

    def create_or_update_static_route(
        self, tier0_id: str, route_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", route_id)
        return self._create_or_update(
            f"/infra/tier-0s/{tier0_id}/static-routes/{route_id}", spec
        )

    def delete_static_route(self, tier0_id: str, route_id: str) -> None:
        self._delete(f"/infra/tier-0s/{tier0_id}/static-routes/{route_id}")

    # BGP Config

    def get_bgp(self, tier0_id: str, ls_id: str) -> BGPConfig:
        return self._get(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/bgp", BGPConfig
        )

    def set_bgp(self, tier0_id: str, ls_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        return self._create_or_update(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/bgp", spec
        )

    # BGP Neighbors

    def list_bgp_neighbors(self, tier0_id: str, ls_id: str) -> List[BGPNeighbor]:
        return self._list(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/bgp/neighbors",
            BGPNeighbor,
        )

    def get_bgp_neighbor(self, tier0_id: str, ls_id: str, neighbor_id: str) -> BGPNeighbor:
        return self._get(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/bgp/neighbors/{neighbor_id}",
            BGPNeighbor,
        )

    def create_or_update_bgp_neighbor(
        self, tier0_id: str, ls_id: str, neighbor_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", neighbor_id)
        return self._create_or_update(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/bgp/neighbors/{neighbor_id}",
            spec,
        )

    def delete_bgp_neighbor(self, tier0_id: str, ls_id: str, neighbor_id: str) -> None:
        self._delete(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/bgp/neighbors/{neighbor_id}"
        )

    # OSPF

    def get_ospf(self, tier0_id: str, ls_id: str) -> OSPFConfig:
        return self._get(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/ospf", OSPFConfig
        )

    def set_ospf(self, tier0_id: str, ls_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        return self._create_or_update(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/ospf", spec
        )

    def list_ospf_areas(self, tier0_id: str, ls_id: str) -> List[OSPFArea]:
        return self._list(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/ospf/areas", OSPFArea
        )

    def get_ospf_area(self, tier0_id: str, ls_id: str, area_id: str) -> OSPFArea:
        return self._get(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/ospf/areas/{area_id}", OSPFArea
        )

    def create_or_update_ospf_area(
        self, tier0_id: str, ls_id: str, area_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", area_id)
        return self._create_or_update(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/ospf/areas/{area_id}", spec
        )

    def delete_ospf_area(self, tier0_id: str, ls_id: str, area_id: str) -> None:
        self._delete(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}/ospf/areas/{area_id}"
        )

    # Route Redistribution (via locale service PATCH)

    def get_redistribution(self, tier0_id: str, ls_id: str) -> Dict[str, Any]:
        """Get route redistribution config (part of locale service)."""
        ls = self.get_locale_service(tier0_id, ls_id)
        return {"route_redistribution_config": getattr(ls, "route_redistribution_config", None)}

    def set_redistribution(
        self, tier0_id: str, ls_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set route redistribution by patching the locale service."""
        return self._create_or_update(
            f"/infra/tier-0s/{tier0_id}/locale-services/{ls_id}",
            {"route_redistribution_config": spec},
        )

    # Prefix Lists

    def list_prefix_lists(self, tier0_id: str) -> List[PrefixList]:
        return self._list(f"/infra/tier-0s/{tier0_id}/prefix-lists", PrefixList)

    def get_prefix_list(self, tier0_id: str, pl_id: str) -> PrefixList:
        return self._get(f"/infra/tier-0s/{tier0_id}/prefix-lists/{pl_id}", PrefixList)

    def create_or_update_prefix_list(
        self, tier0_id: str, pl_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", pl_id)
        return self._create_or_update(f"/infra/tier-0s/{tier0_id}/prefix-lists/{pl_id}", spec)

    def delete_prefix_list(self, tier0_id: str, pl_id: str) -> None:
        self._delete(f"/infra/tier-0s/{tier0_id}/prefix-lists/{pl_id}")

    # Community Lists

    def list_community_lists(self, tier0_id: str) -> List[CommunityList]:
        return self._list(f"/infra/tier-0s/{tier0_id}/community-lists", CommunityList)

    def get_community_list(self, tier0_id: str, cl_id: str) -> CommunityList:
        return self._get(f"/infra/tier-0s/{tier0_id}/community-lists/{cl_id}", CommunityList)

    def create_or_update_community_list(
        self, tier0_id: str, cl_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", cl_id)
        return self._create_or_update(f"/infra/tier-0s/{tier0_id}/community-lists/{cl_id}", spec)

    def delete_community_list(self, tier0_id: str, cl_id: str) -> None:
        self._delete(f"/infra/tier-0s/{tier0_id}/community-lists/{cl_id}")

    # Route Maps

    def list_route_maps(self, tier0_id: str) -> List[RouteMap]:
        return self._list(f"/infra/tier-0s/{tier0_id}/route-maps", RouteMap)

    def get_route_map(self, tier0_id: str, rm_id: str) -> RouteMap:
        return self._get(f"/infra/tier-0s/{tier0_id}/route-maps/{rm_id}", RouteMap)

    def create_or_update_route_map(
        self, tier0_id: str, rm_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", rm_id)
        return self._create_or_update(f"/infra/tier-0s/{tier0_id}/route-maps/{rm_id}", spec)

    def delete_route_map(self, tier0_id: str, rm_id: str) -> None:
        self._delete(f"/infra/tier-0s/{tier0_id}/route-maps/{rm_id}")

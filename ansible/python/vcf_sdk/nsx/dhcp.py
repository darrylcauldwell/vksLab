"""DHCP management for NSX-T Policy API."""

from typing import Any, Dict, List

from vcf_sdk.models.nsx import DHCPServerConfig, DHCPRelayConfig
from vcf_sdk.nsx.base import NSXBaseManager


class DHCPManager(NSXBaseManager):
    """Manage DHCP server and relay configurations."""

    # DHCP Server

    def list_servers(self) -> List[DHCPServerConfig]:
        return self._list("/infra/dhcp-server-configs", DHCPServerConfig)

    def get_server(self, config_id: str) -> DHCPServerConfig:
        return self._get(f"/infra/dhcp-server-configs/{config_id}", DHCPServerConfig)

    def create_or_update_server(
        self, config_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", config_id)
        return self._create_or_update(f"/infra/dhcp-server-configs/{config_id}", spec)

    def delete_server(self, config_id: str) -> None:
        self._delete(f"/infra/dhcp-server-configs/{config_id}")

    # DHCP Relay

    def list_relays(self) -> List[DHCPRelayConfig]:
        return self._list("/infra/dhcp-relay-configs", DHCPRelayConfig)

    def get_relay(self, config_id: str) -> DHCPRelayConfig:
        return self._get(f"/infra/dhcp-relay-configs/{config_id}", DHCPRelayConfig)

    def create_or_update_relay(
        self, config_id: str, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        spec.setdefault("id", config_id)
        return self._create_or_update(f"/infra/dhcp-relay-configs/{config_id}", spec)

    def delete_relay(self, config_id: str) -> None:
        self._delete(f"/infra/dhcp-relay-configs/{config_id}")

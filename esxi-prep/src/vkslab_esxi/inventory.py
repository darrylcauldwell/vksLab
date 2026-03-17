"""Lab inventory for managing groups of ESXi hosts."""

from __future__ import annotations

import logging

from vkslab_esxi.config import LabConfig
from vkslab_esxi.host import ESXiHost

logger = logging.getLogger("vkslab_esxi")


class LabInventory:
    """Manages all ESXi hosts in the lab."""

    def __init__(self, config: LabConfig) -> None:
        self.config = config
        self._hosts = [ESXiHost(h, config) for h in config.hosts]

    def all_hosts(self) -> list[ESXiHost]:
        """Return all ESXi hosts."""
        return list(self._hosts)

    def management_hosts(self) -> list[ESXiHost]:
        """Return management domain hosts."""
        return [h for h in self._hosts if h.host.domain == "management"]

    def workload_hosts(self) -> list[ESXiHost]:
        """Return workload domain hosts."""
        return [h for h in self._hosts if h.host.domain == "workload"]

    def get_host(self, name: str) -> ESXiHost | None:
        """Find a host by name."""
        for h in self._hosts:
            if h.host.name == name:
                return h
        return None

    def hosts_by_domain(self, domain: str) -> list[ESXiHost]:
        """Return hosts filtered by domain name ('management', 'workload', or 'all')."""
        if domain == "all":
            return self.all_hosts()
        return [h for h in self._hosts if h.host.domain == domain]

    def prepare_all(self, password: str, *, domain: str = "all") -> dict[str, bool]:
        """Prepare all hosts (or filtered by domain).

        Returns:
            Dict mapping host name to success status.
        """
        hosts = self.hosts_by_domain(domain)
        results = {}
        for host in hosts:
            try:
                host.prepare_full(password)
                results[host.host.name] = True
            except Exception as e:
                logger.error("%s: preparation failed: %s", host.host.name, e)
                results[host.host.name] = False
        return results

"""Tests for lab inventory."""

from vkslab_esxi.config import HostConfig, LabConfig
from vkslab_esxi.inventory import LabInventory


def make_config() -> LabConfig:
    return LabConfig(
        hosts=[
            HostConfig("esxi-01", "10.0.10.11", "aa:bb:01", "management"),
            HostConfig("esxi-02", "10.0.10.12", "aa:bb:02", "management"),
            HostConfig("esxi-03", "10.0.10.13", "aa:bb:03", "management"),
            HostConfig("esxi-04", "10.0.10.14", "aa:bb:04", "management"),
            HostConfig("esxi-05", "10.0.10.15", "aa:bb:05", "workload"),
            HostConfig("esxi-06", "10.0.10.16", "aa:bb:06", "workload"),
            HostConfig("esxi-07", "10.0.10.17", "aa:bb:07", "workload"),
        ]
    )


class TestLabInventory:
    def test_all_hosts(self):
        inv = LabInventory(make_config())
        assert len(inv.all_hosts()) == 7

    def test_management_hosts(self):
        inv = LabInventory(make_config())
        mgmt = inv.management_hosts()
        assert len(mgmt) == 4
        assert all(h.host.domain == "management" for h in mgmt)

    def test_workload_hosts(self):
        inv = LabInventory(make_config())
        wld = inv.workload_hosts()
        assert len(wld) == 3
        assert all(h.host.domain == "workload" for h in wld)

    def test_get_host_found(self):
        inv = LabInventory(make_config())
        host = inv.get_host("esxi-05")
        assert host is not None
        assert host.host.ip == "10.0.10.15"

    def test_get_host_not_found(self):
        inv = LabInventory(make_config())
        assert inv.get_host("nonexistent") is None

    def test_hosts_by_domain_all(self):
        inv = LabInventory(make_config())
        assert len(inv.hosts_by_domain("all")) == 7

    def test_hosts_by_domain_management(self):
        inv = LabInventory(make_config())
        assert len(inv.hosts_by_domain("management")) == 4

    def test_hosts_by_domain_workload(self):
        inv = LabInventory(make_config())
        assert len(inv.hosts_by_domain("workload")) == 3

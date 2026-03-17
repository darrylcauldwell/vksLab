"""Tests for ESXi host operations."""

from unittest.mock import MagicMock, call

import pytest

from vkslab_esxi.config import HostConfig, LabConfig
from vkslab_esxi.host import ESXiHost
from vkslab_esxi.ssh import CommandResult


@pytest.fixture
def lab_config():
    return LabConfig(
        domain="lab.dreamfold.dev",
        gateway="10.0.10.1",
        dns_server="10.0.10.2",
        ntp_servers=["10.0.10.2", "10.0.10.1"],
        vsan_esa_vib_path="/tmp/mock-hcl.vib",
        ca_cert_path="/tmp/lab-root-ca.crt",
    )


@pytest.fixture
def host_config():
    return HostConfig(
        name="esxi-01", ip="10.0.10.11", mac="00:50:56:aa:bb:01", domain="management"
    )


@pytest.fixture
def esxi_host(host_config, lab_config):
    return ESXiHost(host_config, lab_config)


@pytest.fixture
def mock_ssh():
    ssh = MagicMock()
    ssh.run.return_value = CommandResult("cmd", "", "", 0)
    return ssh


class TestConfigureHostname:
    def test_sets_hostname(self, esxi_host, mock_ssh):
        esxi_host.configure_hostname(mock_ssh)
        mock_ssh.run.assert_called_once_with(
            "esxcli system hostname set "
            "--host=esxi-01 "
            "--fqdn=esxi-01.lab.dreamfold.dev "
            "--domain=lab.dreamfold.dev"
        )


class TestConfigureDns:
    def test_adds_dns_server(self, esxi_host, mock_ssh):
        esxi_host.configure_dns(mock_ssh)
        calls = mock_ssh.run.call_args_list
        assert calls[0] == call("esxcli network ip dns server add --server=10.0.10.2")
        assert calls[1] == call(
            "esxcli network ip dns search add --domain=lab.dreamfold.dev"
        )


class TestConfigureNtp:
    def test_sets_dual_ntp(self, esxi_host, mock_ssh):
        esxi_host.configure_ntp(mock_ssh)
        calls = mock_ssh.run.call_args_list
        assert calls[0] == call("esxcli system ntp set --server=10.0.10.2,10.0.10.1")
        assert calls[1] == call("esxcli system ntp set --enabled=true")


class TestSetRootPassword:
    def test_sets_password(self, esxi_host, mock_ssh):
        esxi_host.set_root_password(mock_ssh, "newpass123")
        mock_ssh.run.assert_called_once_with("echo 'root:newpass123' | chpasswd")


class TestParseStorageDevices:
    def test_parse_fixture(self, fixtures_dir):
        output = (fixtures_dir / "storage_device_list.txt").read_text()
        devices = ESXiHost._parse_storage_devices(output)
        assert len(devices) == 2

        nvme = devices[0]
        assert "NVMe" in nvme.device_id
        assert nvme.is_ssd is False
        assert nvme.size_mb == 204800
        assert nvme.is_boot is False

        boot = devices[1]
        assert boot.is_ssd is True
        assert boot.is_boot is True


class TestMarkDeviceAsSsd:
    def test_marks_device(self, esxi_host, mock_ssh):
        esxi_host.mark_device_as_ssd(mock_ssh, "t10.NVMe__VBOX")
        mock_ssh.run.assert_called_once_with(
            "esxcli storage hpp device set -d t10.NVMe__VBOX -M true"
        )


class TestMarkAllDevicesAsSsd:
    def test_marks_nvme_non_boot(self, esxi_host, mock_ssh, fixtures_dir):
        output = (fixtures_dir / "storage_device_list.txt").read_text()
        mock_ssh.run.side_effect = [
            CommandResult("list", output, "", 0),  # list_storage_devices
            CommandResult("mark", "", "", 0),  # mark_device_as_ssd
        ]
        marked = esxi_host.mark_all_devices_as_ssd(mock_ssh)
        assert len(marked) == 1
        assert "NVMe" in marked[0]


class TestSetFakeScsiReservations:
    def test_sets_advanced_setting(self, esxi_host, mock_ssh):
        esxi_host.set_fake_scsi_reservations(mock_ssh)
        mock_ssh.run.assert_called_once_with(
            "esxcli system settings advanced set -o /VSAN/FakeSCSIReservations -i 1"
        )


class TestSetAcceptanceLevel:
    def test_sets_community(self, esxi_host, mock_ssh):
        esxi_host.set_acceptance_level(mock_ssh)
        mock_ssh.run.assert_called_once_with(
            "esxcli software acceptance set --level=CommunitySupported"
        )


class TestInstallMockVib:
    def test_installs_vib(self, esxi_host, mock_ssh):
        esxi_host.install_vsan_esa_mock_vib(mock_ssh, "/tmp/mock-hcl.vib")
        mock_ssh.run.assert_called_once_with(
            "esxcli software vib install -v /tmp/mock-hcl.vib --force --no-sig-check"
        )


class TestRestartVsanMgmt:
    def test_restarts_service(self, esxi_host, mock_ssh):
        esxi_host.restart_vsan_mgmt_service(mock_ssh)
        mock_ssh.run.assert_called_once_with("/etc/init.d/vsanmgmtd restart")


class TestEnableVsanFirewall:
    def test_enables_rules(self, esxi_host, mock_ssh):
        esxi_host.enable_vsan_firewall_rules(mock_ssh)
        calls = mock_ssh.run.call_args_list
        assert calls[0] == call(
            "esxcli network firewall ruleset set -e true -r vsan-transport"
        )
        assert calls[1] == call(
            "esxcli network firewall ruleset set -e true -r vsanEncryption"
        )


class TestPing:
    def test_ping_success(self, esxi_host, mock_ssh):
        mock_ssh.run.return_value = CommandResult("vmkping", "3 packets", "", 0)
        assert esxi_host.ping(mock_ssh, "10.0.10.1") is True

    def test_ping_failure(self, esxi_host, mock_ssh):
        mock_ssh.run.return_value = CommandResult("vmkping", "", "timeout", 1)
        assert esxi_host.ping(mock_ssh, "10.0.10.99") is False


class TestVerifyNetwork:
    def test_checks_gateway_and_dns(self, esxi_host, mock_ssh):
        mock_ssh.run.return_value = CommandResult("vmkping", "ok", "", 0)
        result = esxi_host.verify_network_connectivity(mock_ssh)
        assert result == {"gateway": True, "dns": True}


class TestImportCaCertificate:
    def test_imports_cert(self, esxi_host, mock_ssh):
        esxi_host.import_ca_certificate(mock_ssh, "/tmp/lab-root-ca.crt")
        mock_ssh.run.assert_called_once_with(
            "esxcli security cert import --cert-file /tmp/lab-root-ca.crt"
        )


class TestPrepareVsanEsa:
    def test_runs_full_sequence(self, esxi_host, mock_ssh, fixtures_dir):
        output = (fixtures_dir / "storage_device_list.txt").read_text()
        # Return storage device list for mark_all_devices_as_ssd
        def side_effect(cmd, **kwargs):
            if "storage core device list" in cmd:
                return CommandResult("list", output, "", 0)
            return CommandResult(cmd, "", "", 0)

        mock_ssh.run.side_effect = side_effect
        esxi_host.prepare_vsan_esa(mock_ssh, vib_path="/tmp/mock.vib")

        cmds = [c.args[0] for c in mock_ssh.run.call_args_list]
        assert any("acceptance" in c for c in cmds)
        assert any("vib install" in c for c in cmds)
        assert any("vsanmgmtd restart" in c for c in cmds)
        assert any("FakeSCSIReservations" in c for c in cmds)
        assert any("storage core device list" in c for c in cmds)
        assert any("firewall" in c for c in cmds)

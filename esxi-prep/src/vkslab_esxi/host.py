"""ESXi host configuration operations."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from vkslab_esxi.config import HostConfig, LabConfig
from vkslab_esxi.ssh import SSHConnection

logger = logging.getLogger("vkslab_esxi")


@dataclass
class StorageDevice:
    """Parsed storage device from esxcli output."""

    device_id: str
    display_name: str
    is_ssd: bool
    size_mb: int
    is_boot: bool


class ESXiHost:
    """Operations on a single ESXi host via SSH."""

    def __init__(self, host_config: HostConfig, lab_config: LabConfig) -> None:
        self.host = host_config
        self.lab = lab_config
        self._ssh: SSHConnection | None = None

    def _get_ssh(self, password: str) -> SSHConnection:
        if self._ssh is None:
            self._ssh = SSHConnection(self.host.ip, password=password)
            self._ssh.connect()
        return self._ssh

    def close(self) -> None:
        if self._ssh:
            self._ssh.close()
            self._ssh = None

    def configure_hostname(self, ssh: SSHConnection) -> None:
        """Set ESXi hostname and FQDN."""
        ssh.run(
            f"esxcli system hostname set "
            f"--host={self.host.name} "
            f"--fqdn={self.host.fqdn} "
            f"--domain={self.lab.domain}"
        )
        logger.info("%s: hostname set to %s", self.host.name, self.host.fqdn)

    def configure_dns(self, ssh: SSHConnection) -> None:
        """Configure DNS server."""
        ssh.run(f"esxcli network ip dns server add --server={self.lab.dns_server}")
        ssh.run(
            f"esxcli network ip dns search add --domain={self.lab.domain}"
        )
        logger.info("%s: DNS configured (%s)", self.host.name, self.lab.dns_server)

    def configure_ntp(self, ssh: SSHConnection) -> None:
        """Configure NTP servers (dual: jumpbox + vEOS)."""
        servers = ",".join(self.lab.ntp_servers)
        ssh.run(f"esxcli system ntp set --server={servers}")
        ssh.run("esxcli system ntp set --enabled=true")
        logger.info("%s: NTP configured (%s)", self.host.name, servers)

    def set_root_password(self, ssh: SSHConnection, password: str) -> None:
        """Set root password on ESXi host."""
        ssh.run(f"echo 'root:{password}' | chpasswd")
        logger.info("%s: root password set", self.host.name)

    def list_storage_devices(self, ssh: SSHConnection) -> list[StorageDevice]:
        """List storage devices and parse into StorageDevice objects."""
        result = ssh.run("esxcli storage core device list")
        return self._parse_storage_devices(result.stdout)

    @staticmethod
    def _parse_storage_devices(output: str) -> list[StorageDevice]:
        """Parse esxcli storage core device list output."""
        devices = []
        current: dict[str, str] = {}
        current_id = ""

        for raw_line in output.splitlines():
            if not raw_line.strip():
                continue

            # Property lines are indented (start with spaces); device IDs are not
            if raw_line.startswith("   ") or raw_line.startswith("\t"):
                # This is a property line
                line = raw_line.strip()
                if ":" in line:
                    key, _, value = line.partition(":")
                    current[key.strip()] = value.strip()
            else:
                # This is a device ID header
                if current_id and current:
                    devices.append(
                        StorageDevice(
                            device_id=current_id,
                            display_name=current.get("Display Name", ""),
                            is_ssd=current.get("Is SSD", "false").lower() == "true",
                            size_mb=int(current.get("Size", "0")),
                            is_boot=current.get("Is Boot Device", "false").lower()
                            == "true",
                        )
                    )
                current_id = raw_line.strip()
                current = {}

        # Don't forget the last device
        if current_id and current:
            devices.append(
                StorageDevice(
                    device_id=current_id,
                    display_name=current.get("Display Name", ""),
                    is_ssd=current.get("Is SSD", "false").lower() == "true",
                    size_mb=int(current.get("Size", "0")),
                    is_boot=current.get("Is Boot Device", "false").lower() == "true",
                )
            )

        return devices

    def mark_device_as_ssd(self, ssh: SSHConnection, device_id: str) -> None:
        """Mark a specific storage device as SSD."""
        ssh.run(f"esxcli storage hpp device set -d {device_id} -M true")
        logger.info("%s: marked %s as SSD", self.host.name, device_id)

    def mark_all_devices_as_ssd(self, ssh: SSHConnection) -> list[str]:
        """Discover and mark all non-boot NVMe devices as SSD."""
        devices = self.list_storage_devices(ssh)
        marked = []
        for dev in devices:
            if not dev.is_boot and not dev.is_ssd and "NVMe" in dev.display_name:
                self.mark_device_as_ssd(ssh, dev.device_id)
                marked.append(dev.device_id)
        return marked

    def set_fake_scsi_reservations(self, ssh: SSHConnection) -> None:
        """Enable FakeSCSIReservations for nested vSAN."""
        ssh.run(
            "esxcli system settings advanced set "
            "-o /VSAN/FakeSCSIReservations -i 1"
        )
        logger.info("%s: FakeSCSIReservations enabled", self.host.name)

    def set_acceptance_level(self, ssh: SSHConnection, level: str = "CommunitySupported") -> None:
        """Set ESXi software acceptance level."""
        ssh.run(f"esxcli software acceptance set --level={level}")
        logger.info("%s: acceptance level set to %s", self.host.name, level)

    def install_vsan_esa_mock_vib(self, ssh: SSHConnection, vib_path: str) -> None:
        """Install mock HCL VIB for vSAN ESA in nested environments."""
        ssh.run(f"esxcli software vib install -v {vib_path} --force --no-sig-check")
        logger.info("%s: mock HCL VIB installed", self.host.name)

    def restart_vsan_mgmt_service(self, ssh: SSHConnection) -> None:
        """Restart vSAN management daemon."""
        ssh.run("/etc/init.d/vsanmgmtd restart")
        logger.info("%s: vSAN management service restarted", self.host.name)

    def enable_vsan_firewall_rules(self, ssh: SSHConnection) -> None:
        """Enable vSAN-related firewall rules."""
        ssh.run("esxcli network firewall ruleset set -e true -r vsan-transport")
        ssh.run("esxcli network firewall ruleset set -e true -r vsanEncryption")
        logger.info("%s: vSAN firewall rules enabled", self.host.name)

    def ping(self, ssh: SSHConnection, target: str, vmk: str = "vmk0") -> bool:
        """Test network connectivity via vmkping."""
        result = ssh.run(f"vmkping -I {vmk} {target} -c 3", check=False)
        return result.success

    def verify_network_connectivity(self, ssh: SSHConnection) -> dict[str, bool]:
        """Verify connectivity to gateway and DNS server."""
        return {
            "gateway": self.ping(ssh, self.lab.gateway),
            "dns": self.ping(ssh, self.lab.dns_server),
        }

    def import_ca_certificate(
        self, ssh: SSHConnection, cert_path: str = "/tmp/lab-root-ca.crt"
    ) -> None:
        """Import CA root certificate."""
        ssh.run(f"esxcli security cert import --cert-file {cert_path}")
        logger.info("%s: CA certificate imported", self.host.name)

    def prepare_vsan_esa(self, ssh: SSHConnection, vib_path: str | None = None) -> None:
        """Run full vSAN ESA preparation sequence."""
        self.set_acceptance_level(ssh, "CommunitySupported")
        if vib_path:
            self.install_vsan_esa_mock_vib(ssh, vib_path)
        self.restart_vsan_mgmt_service(ssh)
        self.set_fake_scsi_reservations(ssh)
        self.mark_all_devices_as_ssd(ssh)
        self.enable_vsan_firewall_rules(ssh)
        logger.info("%s: vSAN ESA preparation complete", self.host.name)

    def prepare_full(self, password: str) -> None:
        """Run complete host preparation sequence."""
        ssh = self._get_ssh(password)
        try:
            self.configure_hostname(ssh)
            self.configure_dns(ssh)
            self.configure_ntp(ssh)
            self.set_root_password(ssh, password)
            self.prepare_vsan_esa(ssh, vib_path=self.lab.vsan_esa_vib_path)
            if self.lab.ca_cert_path:
                self.import_ca_certificate(ssh, self.lab.ca_cert_path)
            connectivity = self.verify_network_connectivity(ssh)
            if not all(connectivity.values()):
                logger.warning(
                    "%s: connectivity check failed: %s", self.host.name, connectivity
                )
            logger.info("%s: full preparation complete", self.host.name)
        finally:
            self.close()

"""Lab configuration loading with password resolution."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from vkslab_esxi.exceptions import ConfigError
from vkslab_esxi.secrets import SecretClient

logger = logging.getLogger("vkslab_esxi")

DEFAULT_CONFIG_PATHS = [
    Path("configs/lab.yaml"),
    Path("esxi-prep/configs/lab.yaml"),
    Path.home() / ".config" / "vkslab" / "lab.yaml",
]


@dataclass
class HostConfig:
    """Configuration for a single ESXi host."""

    name: str
    ip: str
    mac: str
    domain: str  # 'management' or 'workload'

    @property
    def fqdn(self) -> str:
        return f"{self.name}.lab.dreamfold.dev"


@dataclass
class LabConfig:
    """Full lab configuration loaded from YAML."""

    domain: str = "lab.dreamfold.dev"
    gateway: str = "10.0.10.1"
    dns_server: str = "10.0.10.2"
    ntp_servers: list[str] = field(default_factory=lambda: ["10.0.10.2", "10.0.10.1"])
    esxi_password: str | None = None
    ca_cert_path: str | None = None
    vsan_esa_vib_path: str | None = None
    openbao_url: str = "http://127.0.0.1:8200"
    openbao_secret_path: str = "secret/esxi/root-password"
    hosts: list[HostConfig] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: str | Path) -> LabConfig:
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")

        try:
            data = yaml.safe_load(path.read_text())
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {path}: {e}") from e

        if not isinstance(data, dict):
            raise ConfigError(f"Expected YAML dict in {path}, got {type(data).__name__}")

        hosts = [
            HostConfig(
                name=h["name"],
                ip=h["ip"],
                mac=h.get("mac", ""),
                domain=h.get("domain", "management"),
            )
            for h in data.get("hosts", [])
        ]

        openbao = data.get("openbao", {})

        return cls(
            domain=data.get("domain", "lab.dreamfold.dev"),
            gateway=data.get("gateway", "10.0.10.1"),
            dns_server=data.get("dns_server", "10.0.10.2"),
            ntp_servers=data.get("ntp_servers", ["10.0.10.2", "10.0.10.1"]),
            esxi_password=data.get("esxi_password"),
            ca_cert_path=data.get("ca_cert_path"),
            vsan_esa_vib_path=data.get("vsan_esa_vib_path"),
            openbao_url=openbao.get("url", "http://127.0.0.1:8200"),
            openbao_secret_path=openbao.get("secret_path", "secret/esxi/root-password"),
            hosts=hosts,
        )

    @classmethod
    def find_and_load(cls, config_path: str | Path | None = None) -> LabConfig:
        """Find and load config from default or specified path."""
        if config_path:
            return cls.from_yaml(config_path)

        for path in DEFAULT_CONFIG_PATHS:
            if path.exists():
                logger.info("Using config: %s", path)
                return cls.from_yaml(path)

        raise ConfigError(
            f"No config file found. Searched: {', '.join(str(p) for p in DEFAULT_CONFIG_PATHS)}"
        )

    def resolve_password(self, *, interactive: bool = False) -> str:
        """Resolve ESXi root password using the priority chain.

        Resolution order:
        1. OpenBao secret store
        2. VKSLAB_ESXI_PASSWORD environment variable
        3. Value in YAML config
        4. Interactive prompt (if interactive=True)
        """
        # 1. OpenBao
        secret_client = SecretClient(url=self.openbao_url)
        if secret_client.available:
            password = secret_client.read(self.openbao_secret_path)
            if password:
                logger.debug("Password resolved from OpenBao")
                return password

        # 2. Environment variable
        env_password = os.environ.get("VKSLAB_ESXI_PASSWORD")
        if env_password:
            logger.debug("Password resolved from VKSLAB_ESXI_PASSWORD")
            return env_password

        # 3. YAML config value
        if self.esxi_password and self.esxi_password != "<CHANGE-ME>":
            logger.debug("Password resolved from config file")
            return self.esxi_password

        # 4. Interactive prompt
        if interactive:
            import getpass

            password = getpass.getpass("ESXi root password: ")
            if password:
                return password

        raise ConfigError(
            "No ESXi password found. Set via OpenBao, VKSLAB_ESXI_PASSWORD env var, "
            "or esxi_password in config YAML."
        )

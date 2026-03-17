"""Tests for config loading and password resolution."""

from unittest.mock import patch

import pytest

from vkslab_esxi.config import HostConfig, LabConfig
from vkslab_esxi.exceptions import ConfigError


class TestHostConfig:
    def test_fqdn(self):
        host = HostConfig(
            name="esxi-01", ip="10.0.10.11", mac="00:50:56:aa:bb:01", domain="management"
        )
        assert host.fqdn == "esxi-01.lab.dreamfold.dev"


class TestLabConfig:
    def test_from_yaml(self, sample_config):
        config = LabConfig.from_yaml(sample_config)
        assert config.domain == "lab.dreamfold.dev"
        assert config.gateway == "10.0.10.1"
        assert config.dns_server == "10.0.10.2"
        assert config.ntp_servers == ["10.0.10.2", "10.0.10.1"]
        assert len(config.hosts) == 7

    def test_from_yaml_hosts(self, sample_config):
        config = LabConfig.from_yaml(sample_config)
        mgmt_hosts = [h for h in config.hosts if h.domain == "management"]
        wld_hosts = [h for h in config.hosts if h.domain == "workload"]
        assert len(mgmt_hosts) == 4
        assert len(wld_hosts) == 3

    def test_from_yaml_missing_file(self, tmp_path):
        with pytest.raises(ConfigError, match="not found"):
            LabConfig.from_yaml(tmp_path / "nonexistent.yaml")

    def test_from_yaml_invalid_yaml(self, tmp_path):
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("{{invalid yaml")
        with pytest.raises(ConfigError, match="Invalid YAML"):
            LabConfig.from_yaml(bad_file)

    def test_from_yaml_not_dict(self, tmp_path):
        list_file = tmp_path / "list.yaml"
        list_file.write_text("- item1\n- item2\n")
        with pytest.raises(ConfigError, match="Expected YAML dict"):
            LabConfig.from_yaml(list_file)

    def test_defaults(self):
        config = LabConfig()
        assert config.domain == "lab.dreamfold.dev"
        assert config.ntp_servers == ["10.0.10.2", "10.0.10.1"]

    def test_find_and_load_explicit_path(self, sample_config):
        config = LabConfig.find_and_load(sample_config)
        assert len(config.hosts) == 7

    def test_find_and_load_no_config(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ConfigError, match="No config file found"):
            LabConfig.find_and_load()


class TestPasswordResolution:
    def test_env_var(self, sample_config, monkeypatch):
        monkeypatch.setenv("VKSLAB_ESXI_PASSWORD", "envpass123")
        config = LabConfig.from_yaml(sample_config)
        password = config.resolve_password()
        assert password == "envpass123"

    def test_yaml_value(self, sample_config, monkeypatch):
        monkeypatch.delenv("VKSLAB_ESXI_PASSWORD", raising=False)
        config = LabConfig.from_yaml(sample_config)
        password = config.resolve_password()
        assert password == "testpass123"

    def test_yaml_placeholder_skipped(self, tmp_path, monkeypatch):
        monkeypatch.delenv("VKSLAB_ESXI_PASSWORD", raising=False)
        cfg = tmp_path / "lab.yaml"
        cfg.write_text("esxi_password: '<CHANGE-ME>'\nhosts: []\n")
        config = LabConfig.from_yaml(cfg)
        with pytest.raises(ConfigError, match="No ESXi password found"):
            config.resolve_password()

    @patch("vkslab_esxi.config.SecretClient")
    def test_openbao_priority(self, mock_secret_class, sample_config, monkeypatch):
        monkeypatch.setenv("VKSLAB_ESXI_PASSWORD", "envpass")
        mock_client = mock_secret_class.return_value
        mock_client.available = True
        mock_client.read.return_value = "bao_password"

        config = LabConfig.from_yaml(sample_config)
        password = config.resolve_password()
        assert password == "bao_password"

    def test_no_password_raises(self, tmp_path, monkeypatch):
        monkeypatch.delenv("VKSLAB_ESXI_PASSWORD", raising=False)
        cfg = tmp_path / "lab.yaml"
        cfg.write_text("hosts: []\n")
        config = LabConfig.from_yaml(cfg)
        with pytest.raises(ConfigError, match="No ESXi password found"):
            config.resolve_password()

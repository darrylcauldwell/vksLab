"""Tests for CLI interface."""

from unittest.mock import patch

from click.testing import CliRunner

from vkslab_esxi.cli import cli


class TestCli:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "VKS Lab ESXi host preparation tool" in result.output

    def test_status_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--domain" in result.output

    def test_prepare_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["prepare", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--domain" in result.output

    def test_storage_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["storage", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.output

    def test_verify_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["verify", "--help"])
        assert result.exit_code == 0

    def test_mark_ssd_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["mark-ssd", "--help"])
        assert result.exit_code == 0
        assert "--device" in result.output

    def test_install_vib_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["install-vib", "--help"])
        assert result.exit_code == 0
        assert "--vib-path" in result.output

    @patch("vkslab_esxi.cli.LabConfig.find_and_load")
    def test_status_with_config(self, mock_load, sample_config):
        from vkslab_esxi.config import LabConfig

        mock_load.return_value = LabConfig.from_yaml(sample_config)

        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "esxi-01" in result.output
        assert "10.0.10.11" in result.output

    @patch("vkslab_esxi.cli.LabConfig.find_and_load")
    def test_status_host_filter(self, mock_load, sample_config):
        from vkslab_esxi.config import LabConfig

        mock_load.return_value = LabConfig.from_yaml(sample_config)

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--host", "esxi-01"])
        assert result.exit_code == 0
        assert "esxi-01" in result.output

    @patch("vkslab_esxi.cli.LabConfig.find_and_load")
    def test_status_host_not_found(self, mock_load, sample_config):
        from vkslab_esxi.config import LabConfig

        mock_load.return_value = LabConfig.from_yaml(sample_config)

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--host", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output

    @patch("vkslab_esxi.cli.LabConfig.find_and_load")
    def test_status_domain_filter(self, mock_load, sample_config):
        from vkslab_esxi.config import LabConfig

        mock_load.return_value = LabConfig.from_yaml(sample_config)

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--domain", "workload"])
        assert result.exit_code == 0
        assert "esxi-05" in result.output

    def test_no_config_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 1
        assert "Error loading config" in result.output

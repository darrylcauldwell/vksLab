"""Tests for SSH connection wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from vkslab_esxi.exceptions import CommandError, SSHConnectionError
from vkslab_esxi.ssh import CommandResult, SSHConnection


class TestCommandResult:
    def test_success_true(self):
        result = CommandResult("ls", "output", "", 0)
        assert result.success is True

    def test_success_false(self):
        result = CommandResult("ls", "", "error", 1)
        assert result.success is False


class TestSSHConnection:
    @patch("vkslab_esxi.ssh.paramiko.SSHClient")
    def test_connect(self, mock_ssh_class):
        conn = SSHConnection("10.0.10.11", password="testpass")
        conn.connect()
        mock_ssh_class.return_value.connect.assert_called_once_with(
            hostname="10.0.10.11",
            username="root",
            password="testpass",
            timeout=30,
            allow_agent=False,
            look_for_keys=False,
        )

    @patch("vkslab_esxi.ssh.paramiko.SSHClient")
    def test_connect_failure(self, mock_ssh_class):
        mock_ssh_class.return_value.connect.side_effect = Exception("Connection refused")
        conn = SSHConnection("10.0.10.11", password="testpass")
        with pytest.raises(SSHConnectionError, match="Connection refused"):
            conn.connect()

    @patch("vkslab_esxi.ssh.paramiko.SSHClient")
    def test_context_manager(self, mock_ssh_class):
        with SSHConnection("10.0.10.11", password="testpass") as conn:
            assert conn._client is not None
        mock_ssh_class.return_value.close.assert_called_once()

    @patch("vkslab_esxi.ssh.paramiko.SSHClient")
    def test_run_success(self, mock_ssh_class):
        mock_client = mock_ssh_class.return_value
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"hostname123"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        conn = SSHConnection("10.0.10.11", password="testpass")
        conn.connect()
        result = conn.run("hostname")

        assert result.stdout == "hostname123"
        assert result.exit_code == 0
        assert result.success is True

    @patch("vkslab_esxi.ssh.paramiko.SSHClient")
    def test_run_failure_raises(self, mock_ssh_class):
        mock_client = mock_ssh_class.return_value
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"command not found"
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        conn = SSHConnection("10.0.10.11", password="testpass")
        conn.connect()
        with pytest.raises(CommandError, match="command not found"):
            conn.run("badcmd")

    @patch("vkslab_esxi.ssh.paramiko.SSHClient")
    def test_run_failure_no_check(self, mock_ssh_class):
        mock_client = mock_ssh_class.return_value
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"error"
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        conn = SSHConnection("10.0.10.11", password="testpass")
        conn.connect()
        result = conn.run("badcmd", check=False)
        assert result.exit_code == 1
        assert result.success is False

    def test_run_not_connected(self):
        conn = SSHConnection("10.0.10.11", password="testpass")
        with pytest.raises(SSHConnectionError, match="Not connected"):
            conn.run("hostname")

    @patch("vkslab_esxi.ssh.paramiko.SSHClient")
    def test_upload_file(self, mock_ssh_class):
        mock_sftp = MagicMock()
        mock_ssh_class.return_value.open_sftp.return_value = mock_sftp

        conn = SSHConnection("10.0.10.11", password="testpass")
        conn.connect()
        conn.upload_file("/tmp/test.vib", "/tmp/remote.vib")

        mock_sftp.put.assert_called_once_with("/tmp/test.vib", "/tmp/remote.vib")
        mock_sftp.close.assert_called_once()

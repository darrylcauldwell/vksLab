"""SSH connection wrapper for ESXi hosts."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Self

import paramiko

from vkslab_esxi.exceptions import CommandError, SSHConnectionError

logger = logging.getLogger("vkslab_esxi")


@dataclass
class CommandResult:
    """Result of a remote command execution."""

    command: str
    stdout: str
    stderr: str
    exit_code: int

    @property
    def success(self) -> bool:
        return self.exit_code == 0


class SSHConnection:
    """Paramiko-based SSH connection to an ESXi host."""

    def __init__(self, hostname: str, username: str = "root", password: str | None = None) -> None:
        self.hostname = hostname
        self.username = username
        self.password = password
        self._client: paramiko.SSHClient | None = None

    def connect(self) -> None:
        """Establish SSH connection."""
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._client.connect(
                hostname=self.hostname,
                username=self.username,
                password=self.password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False,
            )
            logger.debug("SSH connected to %s", self.hostname)
        except Exception as e:
            raise SSHConnectionError(f"Failed to connect to {self.hostname}: {e}") from e

    def close(self) -> None:
        """Close SSH connection."""
        if self._client:
            self._client.close()
            self._client = None
            logger.debug("SSH disconnected from %s", self.hostname)

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def run(self, command: str, *, check: bool = True) -> CommandResult:
        """Execute a command on the remote host.

        Args:
            command: Shell command to execute.
            check: If True, raise CommandError on non-zero exit code.

        Returns:
            CommandResult with stdout, stderr, and exit code.
        """
        if not self._client:
            raise SSHConnectionError(f"Not connected to {self.hostname}")

        logger.debug("Running on %s: %s", self.hostname, command)
        _, stdout_ch, stderr_ch = self._client.exec_command(command)
        exit_code = stdout_ch.channel.recv_exit_status()
        stdout = stdout_ch.read().decode("utf-8", errors="replace").strip()
        stderr = stderr_ch.read().decode("utf-8", errors="replace").strip()

        result = CommandResult(
            command=command,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
        )

        if check and not result.success:
            raise CommandError(command, exit_code, stderr)

        return result

    def upload_file(self, local_path: str | Path, remote_path: str) -> None:
        """Upload a file to the remote host via SFTP."""
        if not self._client:
            raise SSHConnectionError(f"Not connected to {self.hostname}")

        sftp = self._client.open_sftp()
        try:
            sftp.put(str(local_path), remote_path)
            logger.debug("Uploaded %s to %s:%s", local_path, self.hostname, remote_path)
        finally:
            sftp.close()

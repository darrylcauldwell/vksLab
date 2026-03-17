"""Exception hierarchy for vkslab-esxi."""


class VksLabError(Exception):
    """Base exception for all vkslab-esxi errors."""


class SSHConnectionError(VksLabError):
    """Failed to establish SSH connection to ESXi host."""


class CommandError(VksLabError):
    """Remote command execution failed."""

    def __init__(self, command: str, exit_code: int, stderr: str) -> None:
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(f"Command '{command}' failed (exit {exit_code}): {stderr}")


class ConfigError(VksLabError):
    """Configuration loading or validation error."""


class SecretError(VksLabError):
    """Secret store access error."""

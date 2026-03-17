"""OpenBao/Vault secret store client."""

from __future__ import annotations

import logging
import os

from vkslab_esxi.exceptions import SecretError

logger = logging.getLogger("vkslab_esxi")


class SecretClient:
    """Wrapper around hvac for OpenBao/Vault KV v2 access."""

    def __init__(self, url: str = "http://127.0.0.1:8200", token: str | None = None) -> None:
        self.url = url
        self.token = token or os.environ.get("BAO_TOKEN") or os.environ.get("VAULT_TOKEN")
        self._client = None

    def _get_client(self):
        """Lazy-initialise the hvac client."""
        if self._client is None:
            try:
                import hvac

                self._client = hvac.Client(url=self.url, token=self.token)
            except ImportError:
                raise SecretError("hvac package not installed — cannot access OpenBao") from None
        return self._client

    @property
    def available(self) -> bool:
        """Check if the secret store is reachable and authenticated."""
        if not self.token:
            return False
        try:
            client = self._get_client()
            return client.is_authenticated()
        except Exception:
            return False

    def read(self, path: str) -> str | None:
        """Read a secret value from KV v2.

        Args:
            path: Secret path, e.g. 'secret/esxi/root-password'

        Returns:
            The 'value' field of the secret, or None if not found.
        """
        try:
            client = self._get_client()
            # Split: 'secret/esxi/root-password' → mount='secret', path='esxi/root-password'
            parts = path.split("/", 1)
            if len(parts) < 2:
                raise SecretError(f"Invalid secret path: {path}")
            mount, secret_path = parts
            response = client.secrets.kv.v2.read_secret_version(
                path=secret_path,
                mount_point=mount,
            )
            data = response.get("data", {}).get("data", {})
            return data.get("value")
        except SecretError:
            raise
        except Exception as e:
            logger.debug("Failed to read secret %s: %s", path, e)
            return None

    def write(self, path: str, value: str) -> None:
        """Write a secret value to KV v2.

        Args:
            path: Secret path, e.g. 'secret/esxi/root-password'
            value: The value to store.
        """
        try:
            client = self._get_client()
            parts = path.split("/", 1)
            if len(parts) < 2:
                raise SecretError(f"Invalid secret path: {path}")
            mount, secret_path = parts
            client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret={"value": value},
                mount_point=mount,
            )
            logger.debug("Wrote secret to %s", path)
        except SecretError:
            raise
        except Exception as e:
            raise SecretError(f"Failed to write secret {path}: {e}") from e

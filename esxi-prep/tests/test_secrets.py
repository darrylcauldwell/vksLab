"""Tests for OpenBao secret store client."""

from unittest.mock import MagicMock, patch

from vkslab_esxi.secrets import SecretClient


class TestSecretClient:
    def test_not_available_without_token(self):
        client = SecretClient(token=None)
        assert client.available is False

    @patch("vkslab_esxi.secrets.SecretClient._get_client")
    def test_available_with_auth(self, mock_get):
        mock_hvac = MagicMock()
        mock_hvac.is_authenticated.return_value = True
        mock_get.return_value = mock_hvac

        client = SecretClient(token="test-token")
        assert client.available is True

    @patch("vkslab_esxi.secrets.SecretClient._get_client")
    def test_read_secret(self, mock_get):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "my-password"}}
        }
        mock_get.return_value = mock_hvac

        client = SecretClient(token="test-token")
        result = client.read("secret/esxi/root-password")

        assert result == "my-password"
        mock_hvac.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="esxi/root-password",
            mount_point="secret",
        )

    @patch("vkslab_esxi.secrets.SecretClient._get_client")
    def test_read_missing_returns_none(self, mock_get):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.side_effect = Exception("not found")
        mock_get.return_value = mock_hvac

        client = SecretClient(token="test-token")
        result = client.read("secret/missing/path")
        assert result is None

    @patch("vkslab_esxi.secrets.SecretClient._get_client")
    def test_write_secret(self, mock_get):
        mock_hvac = MagicMock()
        mock_get.return_value = mock_hvac

        client = SecretClient(token="test-token")
        client.write("secret/esxi/root-password", "new-password")

        mock_hvac.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
            path="esxi/root-password",
            secret={"value": "new-password"},
            mount_point="secret",
        )

    def test_token_from_env(self, monkeypatch):
        monkeypatch.setenv("BAO_TOKEN", "env-token")
        client = SecretClient()
        assert client.token == "env-token"

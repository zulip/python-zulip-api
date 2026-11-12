import unittest
from unittest.mock import MagicMock, patch

from zulip import AuthenticationError, Client, ZulipError


class TestCheckCredentials(unittest.TestCase):
    @patch(
        "zulip.Client.get_server_settings",
        return_value={"zulip_version": "8.0", "zulip_feature_level": 200},
    )
    def _create_mock_client(
        self, mock_server_settings: MagicMock, check_credentials: bool = False
    ) -> Client:
        return Client(
            email="bot@example.com",
            api_key="secret",
            site="https://zulip.example.com",
            check_credentials=check_credentials,
        )

    def test_check_credentials_success(self) -> None:
        client = self._create_mock_client()
        expected_profile = {"result": "success", "email": "bot@example.com", "user_id": 10}
        with patch.object(client, "get_profile", return_value=expected_profile) as mock_get_profile:
            result = client.check_credentials()
            self.assertEqual(result, expected_profile)
            mock_get_profile.assert_called_once()

    def test_ping_alias(self) -> None:
        client = self._create_mock_client()
        expected_profile = {"result": "success", "email": "bot@example.com"}
        with patch.object(client, "check_credentials", return_value=expected_profile) as mock_check:
            result = client.ping()
            self.assertEqual(result, expected_profile)
            mock_check.assert_called_once()

    def test_check_credentials_invalid_api_key_code(self) -> None:
        client = self._create_mock_client()
        error_response = {"result": "error", "code": "INVALID_API_KEY", "msg": "Invalid API key"}
        with patch.object(client, "get_profile", return_value=error_response):
            with self.assertRaises(AuthenticationError) as cm:
                client.check_credentials()
            self.assertIn("Invalid API key", str(cm.exception))

    def test_check_credentials_invalid_api_key_msg(self) -> None:
        client = self._create_mock_client()
        error_response = {"result": "error", "msg": "Invalid API key"}
        with patch.object(client, "get_profile", return_value=error_response):
            with self.assertRaises(AuthenticationError) as cm:
                client.check_credentials()
            self.assertIn("Invalid API key", str(cm.exception))

    def test_check_credentials_http_401(self) -> None:
        client = self._create_mock_client()
        error_response = {"result": "http-error", "status_code": 401}
        with patch.object(client, "get_profile", return_value=error_response):
            with self.assertRaises(AuthenticationError) as cm:
                client.check_credentials()
            self.assertIn("401", str(cm.exception))

    def test_check_credentials_generic_error(self) -> None:
        client = self._create_mock_client()
        error_response = {"result": "error", "msg": "Rate limit exceeded"}
        with patch.object(client, "get_profile", return_value=error_response):
            with self.assertRaises(ZulipError) as cm:
                client.check_credentials()
            self.assertIn("Rate limit exceeded", str(cm.exception))

    def test_check_credentials_generic_http_error(self) -> None:
        client = self._create_mock_client()
        error_response = {"result": "http-error", "status_code": 500}
        with patch.object(client, "get_profile", return_value=error_response):
            with self.assertRaises(ZulipError) as cm:
                client.check_credentials()
            self.assertIn("500", str(cm.exception))

    @patch("zulip.Client.check_credentials")
    @patch(
        "zulip.Client.get_server_settings",
        return_value={"zulip_version": "8.0", "zulip_feature_level": 200},
    )
    def test_client_init_check_credentials_true(
        self, mock_settings: MagicMock, mock_check: MagicMock
    ) -> None:
        Client(
            email="bot@example.com",
            api_key="secret",
            site="https://zulip.example.com",
            check_credentials=True,
        )
        mock_check.assert_called_once()

    @patch("zulip.Client.check_credentials")
    @patch(
        "zulip.Client.get_server_settings",
        return_value={"zulip_version": "8.0", "zulip_feature_level": 200},
    )
    def test_client_init_check_credentials_default_false(
        self, mock_settings: MagicMock, mock_check: MagicMock
    ) -> None:
        Client(
            email="bot@example.com",
            api_key="secret",
            site="https://zulip.example.com",
        )
        mock_check.assert_not_called()

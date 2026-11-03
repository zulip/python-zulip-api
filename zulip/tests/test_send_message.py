from typing import Any, Dict
from unittest import TestCase
from unittest.mock import MagicMock, patch

import zulip


class TestSendMessage(TestCase):
    def _create_mock_client(self, feature_level: int) -> zulip.Client:
        with patch.object(
            zulip.Client,
            "get_server_settings",
            return_value={"zulip_version": "8.0", "zulip_feature_level": feature_level},
        ):
            return zulip.Client(
                email="bot@example.com",
                api_key="secret-key",
                site="https://zulip.example.com",
            )

    def test_send_message_direct_on_modern_server(self) -> None:
        client = self._create_mock_client(feature_level=174)
        client.call_endpoint = MagicMock(return_value={"result": "success", "id": 42})  # type: ignore[method-assign]

        message_data = {"type": "direct", "to": [123], "content": "Hello"}
        response = client.send_message(message_data)

        self.assertEqual(response, {"result": "success", "id": 42})
        client.call_endpoint.assert_called_once_with(
            url="messages",
            request={"type": "direct", "to": [123], "content": "Hello"},
        )

    def test_send_message_direct_on_future_server(self) -> None:
        client = self._create_mock_client(feature_level=250)
        client.call_endpoint = MagicMock(return_value={"result": "success", "id": 43})  # type: ignore[method-assign]

        message_data = {"type": "direct", "to": [456], "content": "Direct to future"}
        response = client.send_message(message_data)

        self.assertEqual(response, {"result": "success", "id": 43})
        client.call_endpoint.assert_called_once_with(
            url="messages",
            request={"type": "direct", "to": [456], "content": "Direct to future"},
        )

    def test_send_message_direct_translated_on_legacy_server(self) -> None:
        client = self._create_mock_client(feature_level=173)
        client.call_endpoint = MagicMock(return_value={"result": "success", "id": 44})  # type: ignore[method-assign]

        message_data = {"type": "direct", "to": [123], "content": "Hello"}
        response = client.send_message(message_data)

        self.assertEqual(response, {"result": "success", "id": 44})
        client.call_endpoint.assert_called_once_with(
            url="messages",
            request={"type": "private", "to": [123], "content": "Hello"},
        )

    def test_send_message_direct_translated_on_server_feature_level_zero(self) -> None:
        client = self._create_mock_client(feature_level=0)
        client.call_endpoint = MagicMock(return_value={"result": "success", "id": 45})  # type: ignore[method-assign]

        message_data = {"type": "direct", "to": ["user@example.com"], "content": "Hi"}
        response = client.send_message(message_data)

        self.assertEqual(response, {"result": "success", "id": 45})
        client.call_endpoint.assert_called_once_with(
            url="messages",
            request={"type": "private", "to": ["user@example.com"], "content": "Hi"},
        )

    def test_send_message_private_preserved_on_all_servers(self) -> None:
        for feature_level in (0, 100, 173, 174, 300):
            client = self._create_mock_client(feature_level=feature_level)
            client.call_endpoint = MagicMock(return_value={"result": "success"})  # type: ignore[method-assign]

            message_data = {"type": "private", "to": [123], "content": "Private msg"}
            client.send_message(message_data)
            client.call_endpoint.assert_called_once_with(
                url="messages",
                request={"type": "private", "to": [123], "content": "Private msg"},
            )

    def test_send_message_stream_preserved(self) -> None:
        client = self._create_mock_client(feature_level=170)
        client.call_endpoint = MagicMock(return_value={"result": "success"})  # type: ignore[method-assign]

        message_data = {
            "type": "stream",
            "to": "general",
            "topic": "test",
            "content": "Hello channel",
        }
        client.send_message(message_data)
        client.call_endpoint.assert_called_once_with(
            url="messages",
            request=message_data,
        )

    def test_send_message_does_not_mutate_caller_dict(self) -> None:
        client = self._create_mock_client(feature_level=150)
        client.call_endpoint = MagicMock(return_value={"result": "success"})  # type: ignore[method-assign]

        original: Dict[str, Any] = {"type": "direct", "to": [123], "content": "Don't mutate me"}
        client.send_message(original)

        self.assertEqual(original["type"], "direct")

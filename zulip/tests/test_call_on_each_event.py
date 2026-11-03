from typing import Any, Dict
from unittest import TestCase
from unittest.mock import MagicMock, patch

from typing_extensions import override

import zulip
from zulip import ZulipError


class TestCallOnEachEvent(TestCase):
    @override
    def setUp(self) -> None:
        with patch(
            "zulip.Client.get_server_settings",
            return_value={"result": "success", "zulip_version": "8.0"},
        ):
            self.client = zulip.Client(
                email="test@example.com",
                api_key="secret",
                site="https://zulip.example.com",
            )

    @patch("time.sleep")
    def test_register_unauthorized_fails_fast(self, mock_sleep: MagicMock) -> None:
        self.client.register = MagicMock(  # type: ignore[method-assign]
            return_value={"result": "error", "code": "UNAUTHORIZED", "msg": "Invalid API key"}
        )
        callback = MagicMock()

        with self.assertRaises(ZulipError) as cm:
            self.client.call_on_each_event(callback)

        self.assertEqual(str(cm.exception), "UNAUTHORIZED: Invalid API key")
        mock_sleep.assert_not_called()
        callback.assert_not_called()

    @patch("time.sleep")
    def test_register_bad_request_fails_fast(self, mock_sleep: MagicMock) -> None:
        self.client.register = MagicMock(  # type: ignore[method-assign]
            return_value={
                "result": "error",
                "code": "BAD_REQUEST",
                "msg": "Invalid narrow parameter",
            }
        )
        callback = MagicMock()

        with self.assertRaises(ZulipError) as cm:
            self.client.call_on_each_event(callback)

        self.assertEqual(str(cm.exception), "BAD_REQUEST: Invalid narrow parameter")
        mock_sleep.assert_not_called()
        callback.assert_not_called()

    @patch("time.sleep")
    def test_register_error_without_msg_formats_code(self, mock_sleep: MagicMock) -> None:
        self.client.register = MagicMock(  # type: ignore[method-assign]
            return_value={"result": "error", "code": "UNAUTHORIZED"}
        )
        callback = MagicMock()

        with self.assertRaises(ZulipError) as cm:
            self.client.call_on_each_event(callback)

        self.assertEqual(str(cm.exception), "UNAUTHORIZED")
        mock_sleep.assert_not_called()
        callback.assert_not_called()

    @patch("time.sleep")
    def test_get_events_unauthorized_fails_fast(self, mock_sleep: MagicMock) -> None:
        self.client.register = MagicMock(  # type: ignore[method-assign]
            return_value={"result": "success", "queue_id": "q1", "last_event_id": 10}
        )
        self.client.get_events = MagicMock(  # type: ignore[method-assign]
            return_value={"result": "error", "code": "UNAUTHORIZED", "msg": "API key revoked"}
        )
        callback = MagicMock()

        with self.assertRaises(ZulipError) as cm:
            self.client.call_on_each_event(callback)

        self.assertEqual(str(cm.exception), "UNAUTHORIZED: API key revoked")
        mock_sleep.assert_not_called()
        callback.assert_not_called()

    @patch("time.sleep")
    def test_get_events_bad_request_fails_fast(self, mock_sleep: MagicMock) -> None:
        self.client.register = MagicMock(  # type: ignore[method-assign]
            return_value={"result": "success", "queue_id": "q1", "last_event_id": 10}
        )
        self.client.get_events = MagicMock(  # type: ignore[method-assign]
            return_value={"result": "error", "code": "BAD_REQUEST", "msg": "Bad event request"}
        )
        callback = MagicMock()

        with self.assertRaises(ZulipError) as cm:
            self.client.call_on_each_event(callback)

        self.assertEqual(str(cm.exception), "BAD_REQUEST: Bad event request")
        mock_sleep.assert_not_called()
        callback.assert_not_called()

    @patch("time.sleep")
    def test_get_events_transient_bad_event_queue_id_recovers(self, mock_sleep: MagicMock) -> None:
        self.client.register = MagicMock(  # type: ignore[method-assign]
            side_effect=[
                {"result": "success", "queue_id": "q1", "last_event_id": 10},
                {"result": "success", "queue_id": "q2", "last_event_id": 15},
            ]
        )
        # First call returns BAD_EVENT_QUEUE_ID, second returns an event, then exits via KeyboardInterrupt
        self.client.get_events = MagicMock(  # type: ignore[method-assign]
            side_effect=[
                {"result": "error", "code": "BAD_EVENT_QUEUE_ID", "msg": "Bad event queue id: q1"},
                {
                    "result": "success",
                    "events": [{"id": 16, "type": "message", "content": "hello"}],
                },
                KeyboardInterrupt(),
            ]
        )
        events_received = []

        def callback(event: Dict[str, Any]) -> None:
            events_received.append(event)

        with self.assertRaises(KeyboardInterrupt):
            self.client.call_on_each_event(callback)

        self.assertEqual(self.client.register.call_count, 2)
        mock_sleep.assert_called_with(1)
        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0]["id"], 16)

    @patch("time.sleep")
    def test_call_on_each_message_unauthorized_fails_fast(self, mock_sleep: MagicMock) -> None:
        self.client.register = MagicMock(  # type: ignore[method-assign]
            return_value={"result": "error", "code": "UNAUTHORIZED", "msg": "Invalid API key"}
        )
        callback = MagicMock()

        with self.assertRaises(ZulipError) as cm:
            self.client.call_on_each_message(callback)

        self.assertEqual(str(cm.exception), "UNAUTHORIZED: Invalid API key")
        mock_sleep.assert_not_called()
        callback.assert_not_called()

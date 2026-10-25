from unittest import TestCase
from unittest.mock import patch

from typing_extensions import override

import zulip


class TestMessageEndpoints(TestCase):
    @override
    def setUp(self) -> None:
        with patch.object(
            zulip.Client,
            "get_server_settings",
            return_value={"zulip_version": "8.0", "zulip_feature_level": 250},
        ):
            self.client = zulip.Client(
                email="test@example.com",
                api_key="1234567890abcdef",
                site="https://zulip.example.com",
            )

    def test_update_message_strips_message_id_from_request_payload(self) -> None:
        payload = {
            "message_id": 42,
            "topic": "new topic",
            "content": "updated content",
        }
        with patch.object(
            self.client, "call_endpoint", return_value={"result": "success"}
        ) as mock_call:
            res = self.client.update_message(payload)
            self.assertEqual(res, {"result": "success"})

            # URL path includes message_id, but request body excludes it
            mock_call.assert_called_once_with(
                url="messages/42",
                method="PATCH",
                request={"topic": "new topic", "content": "updated content"},
            )

        # Original dictionary should remain unmutated
        self.assertIn("message_id", payload)
        self.assertEqual(payload["message_id"], 42)

    def test_add_reaction_strips_message_id_from_request_payload(self) -> None:
        payload = {
            "message_id": 100,
            "emoji_name": "joy",
            "emoji_code": "1f602",
            "reaction_type": "unicode_emoji",
        }
        with patch.object(
            self.client, "call_endpoint", return_value={"result": "success"}
        ) as mock_call:
            res = self.client.add_reaction(payload)
            self.assertEqual(res, {"result": "success"})

            mock_call.assert_called_once_with(
                url="messages/100/reactions",
                method="POST",
                request={
                    "emoji_name": "joy",
                    "emoji_code": "1f602",
                    "reaction_type": "unicode_emoji",
                },
            )
        self.assertIn("message_id", payload)

    def test_remove_reaction_strips_message_id_from_request_payload(self) -> None:
        payload = {
            "message_id": 100,
            "emoji_name": "joy",
            "emoji_code": "1f602",
            "reaction_type": "unicode_emoji",
        }
        with patch.object(
            self.client, "call_endpoint", return_value={"result": "success"}
        ) as mock_call:
            res = self.client.remove_reaction(payload)
            self.assertEqual(res, {"result": "success"})

            mock_call.assert_called_once_with(
                url="messages/100/reactions",
                method="DELETE",
                request={
                    "emoji_name": "joy",
                    "emoji_code": "1f602",
                    "reaction_type": "unicode_emoji",
                },
            )
        self.assertIn("message_id", payload)

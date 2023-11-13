import io
from typing import IO, Any, Callable, Dict, List, Optional, Set, Tuple, cast
from unittest import TestCase
from unittest.mock import ANY, MagicMock, create_autospec, patch

from zulip import Client
from zulip_bots.lib import (
    BotHandler,
    ExternalBotHandler,
    StateHandler,
    extract_query_without_mention,
    is_private_message_but_not_group_pm,
    run_message_handler_for_bot,
)


class FakeClient:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.storage: Dict[str, str] = dict()

    def get_profile(self) -> Dict[str, Any]:
        return dict(
            user_id="alice",
            full_name="Alice",
            email="alice@example.com",
            id=42,
        )

    def update_storage(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        new_data = payload["storage"]
        self.storage.update(new_data)

        return dict(
            result="success",
        )

    def get_storage(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return dict(
            result="success",
            storage=self.storage,
        )

    def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        return dict(
            result="success",
        )

    def upload_file(self, file: IO[Any]) -> None:
        pass


class FakeBotHandler:
    def usage(self) -> str:
        return """
            This is a fake bot handler that is used
            to spec BotHandler mocks.
            """

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        pass


class LibTest(TestCase):
    def test_basics(self) -> None:
        client = cast(Client, FakeClient())

        handler = ExternalBotHandler(
            client=client, root_dir=None, bot_details=None, bot_config_file=None
        )

        message: Dict[str, Any] = {}
        handler.send_message(message)

    def test_state_handler(self) -> None:
        client = cast(Client, FakeClient())

        state_handler = StateHandler(client)
        state_handler.put("key", [1, 2, 3])
        val = state_handler.get("key")
        self.assertEqual(val, [1, 2, 3])

        # force us to get non-cached values
        state_handler = StateHandler(client)
        val = state_handler.get("key")
        self.assertEqual(val, [1, 2, 3])

    def test_state_handler_by_mock(self) -> None:
        client = MagicMock()

        state_handler = StateHandler(client)
        client.get_storage.assert_not_called()

        client.update_storage = MagicMock(return_value=dict(result="success"))
        state_handler.put("key", [1, 2, 3])
        client.update_storage.assert_called_with(dict(storage=dict(key="[1, 2, 3]")))

        val = state_handler.get("key")
        client.get_storage.assert_not_called()
        self.assertEqual(val, [1, 2, 3])

        # force us to get non-cached values
        client.get_storage = MagicMock(
            return_value=dict(result="success", storage=dict(non_cached_key="[5]"))
        )
        val = state_handler.get("non_cached_key")
        client.get_storage.assert_called_with({"keys": ["non_cached_key"]})
        self.assertEqual(val, [5])

        # value must already be cached
        client.get_storage = MagicMock()
        val = state_handler.get("non_cached_key")
        client.get_storage.assert_not_called()
        self.assertEqual(val, [5])

    def test_react(self) -> None:
        client = cast(Client, FakeClient())
        handler = ExternalBotHandler(
            client=client, root_dir=None, bot_details=None, bot_config_file=None
        )
        emoji_name = "wave"
        message = {"id": 10}
        expected = {
            "message_id": message["id"],
            "emoji_name": "wave",
            "reaction_type": "unicode_emoji",
        }
        client.add_reaction = MagicMock()  # type: ignore[method-assign]
        handler.react(message, emoji_name)
        client.add_reaction.assert_called_once_with(dict(expected))

    def test_send_reply(self) -> None:
        client = cast(Client, FakeClient())
        profile = client.get_profile()
        handler = ExternalBotHandler(
            client=client, root_dir=None, bot_details=None, bot_config_file=None
        )
        to = {"id": 43}
        expected: List[Tuple[Dict[str, Any], Dict[str, Any], Optional[str]]] = [
            (
                {"type": "private", "display_recipient": [to]},
                {"type": "private", "to": [to["id"]]},
                None,
            ),
            (
                {"type": "private", "display_recipient": [to, profile]},
                {"type": "private", "to": [to["id"], profile["id"]]},
                "widget_content",
            ),
            (
                {"type": "stream", "display_recipient": "Stream name", "subject": "Topic"},
                {"type": "stream", "to": "Stream name", "subject": "Topic"},
                "test widget",
            ),
        ]
        response_text = "Response"
        for test in expected:
            client.send_message = MagicMock()  # type: ignore[method-assign]
            handler.send_reply(test[0], response_text, test[2])
            client.send_message.assert_called_once_with(
                dict(test[1], content=response_text, widget_content=test[2])
            )

    def test_content_and_full_content(self) -> None:
        client = cast(Client, FakeClient())
        client.get_profile()
        ExternalBotHandler(client=client, root_dir=None, bot_details=None, bot_config_file=None)

    def test_run_message_handler_for_bot(self) -> None:
        with patch("zulip_bots.lib.Client", new=FakeClient) as fake_client:
            mock_lib_module = MagicMock()
            # __file__ is not mocked by MagicMock(), so we assign a mock value manually.
            mock_lib_module.__file__ = "foo"
            mock_bot_handler = create_autospec(FakeBotHandler)
            mock_lib_module.handler_class.return_value = mock_bot_handler

            def call_on_each_event_mock(
                self: FakeClient,
                callback: Callable[[Dict[str, Any]], None],
                event_types: Optional[List[str]] = None,
                narrow: Optional[List[List[str]]] = None,
            ) -> None:
                def test_message(message: Dict[str, Any], flags: Set[str]) -> None:
                    event = {"message": message, "flags": flags, "type": "message"}
                    callback(event)

                # In the following test, expected_message is the dict that we expect
                # to be passed to the bot's handle_message function.
                original_message = {"content": "@**Alice** bar", "type": "stream"}
                expected_message = {
                    "type": "stream",
                    "content": "bar",
                    "full_content": "@**Alice** bar",
                }
                test_message(original_message, {"mentioned"})
                mock_bot_handler.handle_message.assert_called_with(
                    message=expected_message, bot_handler=ANY
                )

            fake_client.call_on_each_event = call_on_each_event_mock.__get__(  # type: ignore[attr-defined]
                fake_client, type(fake_client)
            )
            run_message_handler_for_bot(
                lib_module=mock_lib_module,
                quiet=True,
                config_file=None,
                bot_config_file=None,
                bot_name="testbot",
                bot_source="bot code location",
            )

    def test_upload_file(self) -> None:
        client, handler = self._create_client_and_handler_for_file_upload()
        file = io.BytesIO(b"binary")

        handler.upload_file(file)

        client.upload_file.assert_called_once_with(file)  # type: ignore[attr-defined]

    def test_upload_file_from_path(self) -> None:
        client, handler = self._create_client_and_handler_for_file_upload()
        file = io.BytesIO(b"binary")

        with patch("builtins.open", return_value=file):
            handler.upload_file_from_path("file.txt")

        client.upload_file.assert_called_once_with(file)  # type: ignore[attr-defined]

    def test_extract_query_without_mention(self) -> None:
        client = cast(Client, FakeClient())
        handler = ExternalBotHandler(
            client=client, root_dir=None, bot_details=None, bot_config_file=None
        )
        message = {"content": "@**Alice** Hello World"}
        self.assertEqual(extract_query_without_mention(message, handler), "Hello World")
        message = {"content": "@**Alice|alice** Hello World"}
        self.assertEqual(extract_query_without_mention(message, handler), "Hello World")
        message = {"content": "@**Alice Renamed|alice** Hello World"}
        self.assertEqual(extract_query_without_mention(message, handler), "Hello World")
        message = {"content": "Not at start @**Alice|alice** Hello World"}
        self.assertEqual(extract_query_without_mention(message, handler), None)

    def test_is_private_message_but_not_group_pm(self) -> None:
        client = cast(Client, FakeClient())
        handler = ExternalBotHandler(
            client=client, root_dir=None, bot_details=None, bot_config_file=None
        )
        message: Dict[str, Any] = {}
        message["display_recipient"] = "some stream"
        message["type"] = "stream"
        self.assertFalse(is_private_message_but_not_group_pm(message, handler))
        message["type"] = "private"
        message["display_recipient"] = [{"email": "a1@b.com"}]
        message["sender_id"] = handler.user_id
        self.assertFalse(is_private_message_but_not_group_pm(message, handler))
        message["sender_id"] = 0  # someone else
        self.assertTrue(is_private_message_but_not_group_pm(message, handler))
        message["display_recipient"] = [{"email": "a1@b.com"}, {"email": "a2@b.com"}]
        self.assertFalse(is_private_message_but_not_group_pm(message, handler))

    def _create_client_and_handler_for_file_upload(self) -> Tuple[Client, ExternalBotHandler]:
        client = cast(Client, FakeClient())
        client.upload_file = MagicMock()  # type: ignore[method-assign]

        handler = ExternalBotHandler(
            client=client, root_dir=None, bot_details=None, bot_config_file=None
        )
        return client, handler

from unittest.mock import patch

from requests.exceptions import ConnectionError
from typing_extensions import override

from zulip_bots.test_file_utils import get_bot_message_handler
from zulip_bots.test_lib import BotTestCase, DefaultTests, StubBotHandler


class TestGiphyBot(BotTestCase, DefaultTests):
    bot_name = "giphy"

    # Test for bot response to empty message
    @override
    def test_bot_responds_to_empty_message(self) -> None:
        bot_response = (
            "[Click to enlarge]"
            "(https://media0.giphy.com/media/ISumMYQyX4sSI/giphy.gif)"
            "[](/static/images/interactive-bot/giphy/powered-by-giphy.png)"
        )
        with self.mock_config_info({"key": "12345678"}), self.mock_http_conversation("test_random"):
            self.verify_reply("", bot_response)

    def test_normal(self) -> None:
        bot_response = (
            "[Click to enlarge]"
            "(https://media4.giphy.com/media/3o6ZtpxSZbQRRnwCKQ/giphy.gif)"
            "[](/static/images/interactive-bot/giphy/powered-by-giphy.png)"
        )

        with self.mock_config_info({"key": "12345678"}), self.mock_http_conversation("test_normal"):
            self.verify_reply("Hello", bot_response)

    def test_no_result(self) -> None:
        with self.mock_config_info({"key": "12345678"}), self.mock_http_conversation(
            "test_no_result"
        ):
            self.verify_reply(
                "world without zulip",
                'Sorry, I don\'t have a GIF for "world without zulip"! :astonished:',
            )

    def test_invalid_config(self) -> None:
        get_bot_message_handler(self.bot_name)
        StubBotHandler()
        with self.mock_http_conversation("test_403"):
            self.validate_invalid_config(
                {"key": "12345678"}, "This is likely due to an invalid key.\n"
            )

    def test_connection_error_when_validate_config(self) -> None:
        error = ConnectionError()
        with patch("requests.get", side_effect=ConnectionError()):
            self.validate_invalid_config({"key": "12345678"}, str(error))

    def test_valid_config(self) -> None:
        get_bot_message_handler(self.bot_name)
        StubBotHandler()
        with self.mock_http_conversation("test_normal"):
            self.validate_valid_config({"key": "12345678"})

    def test_connection_error_while_running(self) -> None:
        with self.mock_config_info({"key": "12345678"}), patch(
            "requests.get", side_effect=[ConnectionError()]
        ), patch("logging.exception"):
            self.verify_reply(
                "world without chocolate",
                "Uh oh, sorry :slightly_frowning_face:, I "
                "cannot process your request right now. But, "
                "let's try again later! :grin:",
            )

from unittest.mock import patch

from typing_extensions import override

from zulip_bots.bots.link_shortener.link_shortener import LinkShortenerHandler
from zulip_bots.test_lib import BotTestCase, DefaultTests, StubBotHandler


class TestLinkShortenerBot(BotTestCase, DefaultTests):
    bot_name = "link_shortener"

    def _test(self, message: str, response: str) -> None:
        with self.mock_config_info({"key": "qwertyuiop"}):
            self.verify_reply(message, response)

    @override
    def test_bot_responds_to_empty_message(self) -> None:
        with patch("requests.get"):
            self._test(
                "",
                (
                    "No links found. "
                    "Mention the link shortener bot in a conversation and "
                    "then enter any URLs you want to shorten in the body of "
                    "the message."
                ),
            )

    def test_normal(self) -> None:
        with self.mock_http_conversation("test_normal"):
            self._test(
                "Shorten https://www.github.com/zulip/zulip please.",
                "https://www.github.com/zulip/zulip: http://bit.ly/2Ht2hOI",
            )

    def test_no_links(self) -> None:
        # No `mock_http_conversation` is necessary because the bot will
        # recognize that no links are in the message and won't make any HTTP
        # requests.
        with patch("requests.get"):
            self._test(
                "Shorten nothing please.",
                (
                    "No links found. "
                    "Mention the link shortener bot in a conversation and "
                    "then enter any URLs you want to shorten in the body of "
                    "the message."
                ),
            )

    def test_help(self) -> None:
        # No `mock_http_conversation` is necessary because the bot will
        # recognize that the message is 'help' and won't make any HTTP
        # requests.
        with patch("requests.get"):
            self._test(
                "help",
                (
                    "Mention the link shortener bot in a conversation and then "
                    "enter any URLs you want to shorten in the body of the message."
                ),
            )

    def test_exception_when_api_key_is_invalid(self) -> None:
        bot_test_instance = LinkShortenerHandler()
        with self.mock_config_info({"key": "qwertyuiopx"}):
            with self.mock_http_conversation("test_invalid_access_token"):
                with self.assertRaises(StubBotHandler.BotQuitError):
                    bot_test_instance.initialize(StubBotHandler())

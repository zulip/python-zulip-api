from typing import Final
from unittest.mock import patch

from typing_extensions import override

from zulip_bots.test_file_utils import get_bot_message_handler, read_bot_fixture_data
from zulip_bots.test_lib import BotTestCase, DefaultTests, StubBotHandler


class TestTwitpostBot(BotTestCase, DefaultTests):
    bot_name = "twitpost"
    mock_config: Final = {
        "consumer_key": "abcdefghijklmnopqrstuvwxy",
        "consumer_secret": "aabbccddeeffgghhiijjkkllmmnnooppqqrrssttuuvvwwxxyy",
        "access_token": "123456789012345678-ABCDefgh1234afdsa678lKj6gHhslsi",
        "access_token_secret": "yf0SI0x6Ct2OmF0cDQc1E0eLKXrVAPFx4QkZF2f9PfFCt",
    }
    api_response = read_bot_fixture_data("twitpost", "api_response")

    @override
    def test_bot_usage(self) -> None:
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        with self.mock_config_info(self.mock_config):
            bot.initialize(bot_handler)

        self.assertIn("This bot posts on twitter from zulip chat itself", bot.usage())

    @override
    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info(self.mock_config):
            self.verify_reply("", "Please check help for usage.")

    def test_help(self) -> None:
        with self.mock_config_info(self.mock_config):
            self.verify_reply(
                "help",
                "*Help for Twitter-post bot* :twitter: : \n\n"
                "The bot tweets on twitter when message starts with @twitpost.\n\n"
                "`@twitpost tweet <content>` will tweet on twitter with given `<content>`.\n"
                "Example:\n"
                " * @twitpost tweet hey batman\n",
            )

    @patch("tweepy.API.update_status", return_value=api_response)
    def test_tweet(self, mockedarg):
        test_message = "tweet Maybe he'll finally find his keys. #peterfalk"
        bot_response = "Tweet Posted\nhttps://twitter.com/jasoncosta/status/243145735212777472"
        with self.mock_config_info(self.mock_config):
            self.verify_reply(test_message, bot_response)

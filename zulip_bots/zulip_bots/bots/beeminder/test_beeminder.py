from typing import Final
from unittest.mock import patch

from requests.exceptions import ConnectionError
from typing_extensions import override

from zulip_bots.test_file_utils import get_bot_message_handler
from zulip_bots.test_lib import BotTestCase, DefaultTests, StubBotHandler


class TestBeeminderBot(BotTestCase, DefaultTests):
    bot_name = "beeminder"
    normal_config: Final = {"auth_token": "XXXXXX", "username": "aaron", "goalname": "goal"}

    help_message = """
You can add datapoints towards your beeminder goals \
following the syntax shown below :smile:.\n \
\n**@mention-botname daystamp, value, comment**\
\n* `daystamp`**:** *yyyymmdd*  \
[**NOTE:** Optional field, default is *current daystamp*],\
\n* `value`**:** Enter a value [**NOTE:** Required field, can be any number],\
\n* `comment`**:** Add a comment [**NOTE:** Optional field, default is *None*]\
"""

    @override
    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info(self.normal_config), self.mock_http_conversation(
            "test_valid_auth_token"
        ):
            self.verify_reply("", self.help_message)

    def test_help_message(self) -> None:
        with self.mock_config_info(self.normal_config), self.mock_http_conversation(
            "test_valid_auth_token"
        ):
            self.verify_reply("help", self.help_message)

    def test_message_with_daystamp_and_value(self) -> None:
        bot_response = "[Datapoint](https://www.beeminder.com/aaron/goal) created."
        with self.mock_config_info(self.normal_config), self.mock_http_conversation(
            "test_valid_auth_token"
        ), self.mock_http_conversation("test_message_with_daystamp_and_value"):
            self.verify_reply("20180602, 2", bot_response)

    def test_message_with_value_and_comment(self) -> None:
        bot_response = "[Datapoint](https://www.beeminder.com/aaron/goal) created."
        with self.mock_config_info(self.normal_config), self.mock_http_conversation(
            "test_valid_auth_token"
        ), self.mock_http_conversation("test_message_with_value_and_comment"):
            self.verify_reply("2, hi there!", bot_response)

    def test_message_with_daystamp_and_value_and_comment(self) -> None:
        bot_response = "[Datapoint](https://www.beeminder.com/aaron/goal) created."
        with self.mock_config_info(self.normal_config), self.mock_http_conversation(
            "test_valid_auth_token"
        ), self.mock_http_conversation("test_message_with_daystamp_and_value_and_comment"):
            self.verify_reply("20180602, 2, hi there!", bot_response)

    def test_syntax_error(self) -> None:
        with self.mock_config_info(self.normal_config), self.mock_http_conversation(
            "test_valid_auth_token"
        ):
            bot_response = "Make sure you follow the syntax.\n You can take a look \
at syntax by: @mention-botname help"
            self.verify_reply("20180303, 50, comment, redundant comment", bot_response)

    def test_connection_error_when_handle_message(self) -> None:
        with self.mock_config_info(self.normal_config), self.mock_http_conversation(
            "test_valid_auth_token"
        ), patch("requests.post", side_effect=ConnectionError()), patch("logging.exception"):
            self.verify_reply(
                "?$!",
                "Uh-Oh, couldn't process the request \
right now.\nPlease try again later",
            )

    def test_invalid_when_handle_message(self) -> None:
        get_bot_message_handler(self.bot_name)
        StubBotHandler()

        with self.mock_config_info(
            {"auth_token": "someInvalidKey", "username": "aaron", "goalname": "goal"}
        ), patch("requests.get", side_effect=ConnectionError()), self.mock_http_conversation(
            "test_invalid_when_handle_message"
        ), patch("logging.exception"):
            self.verify_reply("5", "Error. Check your key!")

    def test_error(self) -> None:
        bot_request = "notNumber"
        bot_response = "Error occured : 422"
        with self.mock_config_info(self.normal_config), self.mock_http_conversation(
            "test_valid_auth_token"
        ), self.mock_http_conversation("test_error"):
            self.verify_reply(bot_request, bot_response)

    def test_invalid_when_initialize(self) -> None:
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        with self.mock_config_info(
            {"auth_token": "someInvalidKey", "username": "aaron", "goalname": "goal"}
        ), self.mock_http_conversation("test_invalid_when_initialize"), self.assertRaises(
            bot_handler.BotQuitError
        ):
            bot.initialize(bot_handler)

    def test_connection_error_during_initialize(self) -> None:
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        with self.mock_config_info(self.normal_config), patch(
            "requests.get", side_effect=ConnectionError()
        ), patch("logging.exception") as mock_logging:
            bot.initialize(bot_handler)
            self.assertTrue(mock_logging.called)

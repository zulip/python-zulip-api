import unittest
from unittest.mock import patch

from zulip_bots.bots.newsboy.newsboy import NewsboyHandler
from zulip_bots.test_lib import BotTestCase, DefaultTests, StubBotHandler

mock_config = {"api_key": "TEST"}


class Testnewsbot(BotTestCase, DefaultTests):
    bot_name = "newsboy"

    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info(mock_config), patch("requests.get"):
            self.verify_reply("", "Empty Query")

    def test_bot_usage(self) -> None:
        with self.mock_config_info(mock_config), patch("requests.get"):
            self.verify_reply(
                "help",
                """
        ## Newsboy
        The Newsboy bot is a Zulip bot that fetches the top national news of particular country and 
        displays it to the user with headline and short description.

        Use `list-commands` to get information about the supported commands.

        Usage:
        `get-top-news <country-abbreviation>` e.g. `get-top-news us`
        """,
            )

    def test_invalid_command(self) -> None:
        with self.mock_config_info(mock_config), patch("requests.get"):
            self.verify_reply("abcd", "Command not supported")

    def test_list_commands_command(self) -> None:
        expected_reply = (
            "**Commands:** \n"
            "1. **help**: Get the bot usage information.\n"
            "2. **list-commands**: Get information about the commands supported by the bot.\n"
            "3. **get-top-news <country>**: Get top news of mention country e.g. (get-top-news us).\n"
            "4. **list-countries**: Get the list of all supported countries.\n"
        )

        with self.mock_config_info(mock_config), patch("requests.get"):
            self.verify_reply("list-commands", expected_reply)

    def test_command_invalid_arguments(self) -> None:
        """Add appropriate tests here for all additional commands with more than one arguments.
        This ensures consistency."""

        expected_error_response = "Invalid Arguments."

        with self.mock_config_info(mock_config), patch("requests.get"):
            self.verify_reply("get-top-news", expected_error_response)


if __name__ == "__main__":
    unittest.main()

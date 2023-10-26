from typing import Optional
from unittest.mock import patch

from typing_extensions import override

from zulip_bots.test_lib import BotTestCase, DefaultTests


class TestWeatherBot(BotTestCase, DefaultTests):
    bot_name = "weather"

    help_content = """
            This bot returns weather info for specified city.
            You specify city in the following format:
            city, state/country
            state and country parameter is optional(useful when there are many cities with the same name)
            For example:
            @**Weather Bot** Portland
            @**Weather Bot** Portland, Me
            """.strip()

    def _test(self, message: str, response: str, fixture: Optional[str] = None) -> None:
        with self.mock_config_info({"key": "123456"}):
            if fixture:
                with self.mock_http_conversation(fixture):
                    self.verify_reply(message, response)
            else:
                self.verify_reply(message, response)

    # Override default function in BotTestCase
    @override
    def test_bot_responds_to_empty_message(self) -> None:
        with patch("requests.get"):
            self._test("", self.help_content)

    def test_bot(self) -> None:
        # City query
        bot_response = "Weather in New York, US:\n71.33 F / 21.85 C\nMist"
        self._test("New York", bot_response, "test_only_city")

        # City with country query
        bot_response = "Weather in New Delhi, IN:\n80.33 F / 26.85 C\nMist"
        self._test("New Delhi, India", bot_response, "test_city_with_country")

        # Only country query: returns the weather of the capital city
        bot_response = "Weather in London, GB:\n58.73 F / 14.85 C\nShower Rain"
        self._test("United Kingdom", bot_response, "test_only_country")

        # City not found query
        bot_response = "Sorry, city not found"
        self._test("fghjklasdfgh", bot_response, "test_city_not_found")

        # help message
        with patch("requests.get"):
            self._test("help", self.help_content)

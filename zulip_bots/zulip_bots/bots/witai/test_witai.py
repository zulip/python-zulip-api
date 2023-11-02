from typing import Any, Dict, Final, Optional
from unittest.mock import patch

from typing_extensions import override

from zulip_bots.test_file_utils import get_bot_message_handler
from zulip_bots.test_lib import BotTestCase, DefaultTests, StubBotHandler


class TestWitaiBot(BotTestCase, DefaultTests):
    bot_name = "witai"

    MOCK_CONFIG_INFO: Final = {
        "token": "12345678",
        "handler_location": "/Users/abcd/efgh",
        "help_message": "Qwertyuiop!",
    }

    MOCK_WITAI_RESPONSE: Final = {
        "_text": "What is your favorite food?",
        "entities": {"intent": [{"confidence": 1.0, "value": "favorite_food"}]},
    }

    def test_normal(self) -> None:
        with patch("zulip_bots.bots.witai.witai.get_handle", return_value=mock_handle):
            with self.mock_config_info(self.MOCK_CONFIG_INFO):
                get_bot_message_handler(self.bot_name).initialize(StubBotHandler())

                with patch("wit.Wit.message", return_value=self.MOCK_WITAI_RESPONSE):
                    self.verify_reply("What is your favorite food?", "pizza")

    # This overrides the default one in `BotTestCase`.
    @override
    def test_bot_responds_to_empty_message(self) -> None:
        with patch("zulip_bots.bots.witai.witai.get_handle", return_value=mock_handle):
            with self.mock_config_info(self.MOCK_CONFIG_INFO):
                get_bot_message_handler(self.bot_name).initialize(StubBotHandler())
                with patch("wit.Wit.message", return_value=self.MOCK_WITAI_RESPONSE):
                    self.verify_reply("", "Qwertyuiop!")


def mock_handle(res: Dict[str, Any]) -> Optional[str]:
    if res["entities"]["intent"][0]["value"] == "favorite_food":
        return "pizza"
    if res["entities"]["intent"][0]["value"] == "favorite_drink":
        return "coffee"

    return None

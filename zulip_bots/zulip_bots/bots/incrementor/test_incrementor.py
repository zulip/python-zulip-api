from unittest.mock import patch

from zulip_bots.test_file_utils import get_bot_message_handler
from zulip_bots.test_lib import BotTestCase, DefaultTests, StubBotHandler


class TestIncrementorBot(BotTestCase, DefaultTests):
    bot_name = "incrementor"

    def test_bot(self) -> None:
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        message = dict(type="stream")

        bot.initialize(bot_handler)
        bot.handle_message(message, bot_handler)

        with patch("zulip_bots.simple_lib.MockMessageServer.update") as m:
            bot.handle_message(message, bot_handler)
            bot.handle_message(message, bot_handler)
            bot.handle_message(message, bot_handler)

        content_updates = [item[0][0]["content"] for item in m.call_args_list]
        self.assertEqual(content_updates, ["2", "3", "4"])

    def test_bot_edit_timeout(self) -> None:
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        message = dict(type="stream")

        bot.initialize(bot_handler)
        bot.handle_message(message, bot_handler)

        error_msg = dict(msg="The time limit for editing this message has passed", result="error")
        with patch("zulip_bots.test_lib.StubBotHandler.update_message", return_value=error_msg):
            with patch("zulip_bots.simple_lib.MockMessageServer.send") as m:
                bot.handle_message(message, bot_handler)
                bot.handle_message(message, bot_handler)

        # When there is an error, the bot should resend the message with the new value.
        self.assertEqual(m.call_count, 2)

        content_updates = [item[0][0]["content"] for item in m.call_args_list]
        self.assertEqual(content_updates, ["2", "3"])

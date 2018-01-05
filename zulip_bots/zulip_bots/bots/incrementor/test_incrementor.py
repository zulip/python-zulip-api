from unittest import mock

from zulip_bots.test_lib import (
    get_bot_message_handler,
    StubBotHandler,
    BotTestCase,
)

class TestIncrementorBot(BotTestCase):
    bot_name = "incrementor"

    def test_bot(self) -> None:
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        message = dict(type='stream')

        bot.initialize(bot_handler)
        bot.handle_message(message, bot_handler)

        with mock.patch('zulip_bots.simple_lib.SimpleMessageServer.update') as m:
            bot.handle_message(message, bot_handler)
            bot.handle_message(message, bot_handler)
            bot.handle_message(message, bot_handler)

        content_updates = [
            item[0][0]['content']
            for item in m.call_args_list
        ]
        self.assertEqual(content_updates, ['2', '3', '4'])

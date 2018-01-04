from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError, ConnectionError

from typing import Any, Union
from zulip_bots.test_lib import StubBotHandler, BotTestCase, get_bot_message_handler

class TestGiphyBot(BotTestCase):
    bot_name = "giphy"

    # Override default function in BotTestCase
    def test_bot_responds_to_empty_message(self) -> None:
        # FIXME?: Giphy does not respond to empty messages
        pass

    def test_normal(self) -> None:
        bot_response = '[Click to enlarge]' \
                       '(https://media4.giphy.com/media/3o6ZtpxSZbQRRnwCKQ/giphy.gif)' \
                       '[](/static/images/interactive-bot/giphy/powered-by-giphy.png)'

        with self.mock_config_info({'key': '12345678'}), \
                self.mock_http_conversation('test_normal'):
            self.verify_reply('Hello', bot_response)

    def test_no_result(self) -> None:
        with self.mock_config_info({'key': '12345678'}), \
                self.mock_http_conversation('test_no_result'):
            self.verify_reply(
                'world without zulip',
                'Sorry, I don\'t have a GIF for "world without zulip"! :astonished:',
            )

    def test_403(self) -> None:
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        with self.mock_config_info({'key': '12345678'}), \
                self.mock_http_conversation('test_403'),  \
                self.assertRaises(bot_handler.BotQuitException):
            bot.initialize(bot_handler)

    def test_connection_error_while_running(self) -> None:
        with self.mock_config_info({'key': '12345678'}), \
                patch('requests.get', side_effect=[MagicMock(), ConnectionError()]), \
                patch('logging.exception'):
            self.verify_reply(
                'world without chocolate',
                'Uh oh, sorry :slightly_frowning_face:, I '
                'cannot process your request right now. But, '
                'let\'s try again later! :grin:')

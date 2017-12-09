#!/usr/bin/env python

from unittest.mock import patch
from requests.exceptions import HTTPError, ConnectionError

from typing import Any, Union
from zulip_bots.test_lib import StubBotHandler, StubBotTestCase, get_bot_message_handler

class TestGiphyBot(StubBotTestCase):
    bot_name = "giphy"

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

        with self.mock_config_info({'key': '12345678'}):
            bot.initialize(bot_handler)

        mock_message = {'content': 'Hello'}

        with self.mock_http_conversation('test_403'):
            with self.assertRaises(HTTPError):
                # Call the native  handle_message here,
                # since we don't want to assert a response,
                # but an exception.
                bot.handle_message(mock_message, bot_handler)

    def test_connection_error(self) -> None:
        with self.mock_config_info({'key': '12345678'}), \
                patch('requests.get', side_effect=ConnectionError()), \
                patch('logging.exception'):
            self.verify_reply(
                'world without chocolate',
                'Uh oh, sorry :slightly_frowning_face:, I '
                'cannot process your request right now. But, '
                'let\'s try again later! :grin:')

#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import json

from unittest.mock import patch
from requests.exceptions import HTTPError, ConnectionError

from zulip_bots.test_lib import BotTestCase

class TestGiphyBot(BotTestCase):
    bot_name = "giphy"

    def test_normal(self):
        bot_response = '[Click to enlarge]' \
                       '(https://media4.giphy.com/media/3o6ZtpxSZbQRRnwCKQ/giphy.gif)' \
                       '[](/static/images/interactive-bot/giphy/powered-by-giphy.png)'

        with self.mock_config_info({'key': '12345678'}), \
                self.mock_http_conversation('test_normal'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': 'Hello'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

    def test_no_result(self):
        with self.mock_config_info({'key': '12345678'}), \
                self.mock_http_conversation('test_no_result'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': 'world without zulip'},
                response = {'content': 'Sorry, I don\'t have a GIF for "world without zulip"! :astonished:'},
                expected_method='send_reply'
            )

    def test_403(self):
        with self.mock_config_info({'key': '12345678'}), \
                self.mock_http_conversation('test_403'), \
                self.assertRaises(HTTPError):
            self.initialize_bot()
            mock_message = {'content': 'Hello'}
            # Call the native  handle_message here, since we don't want to assert a response,
            # but an exception.
            self.message_handler.handle_message(message={'content': 'Hello'},
                                                bot_handler=self.mock_bot_handler)

    def test_connection_error(self):
        with self.mock_config_info({'key': '12345678'}), \
                patch('requests.get', side_effect=ConnectionError()), \
                patch('logging.warning'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': 'world without chocolate'},
                response = {'content': ('Uh oh, sorry :slightly_frowning_face:, I '
                                        'cannot process your request right now. But, '
                                        'let\'s try again later! :grin:')},
                expected_method='send_reply'
            )

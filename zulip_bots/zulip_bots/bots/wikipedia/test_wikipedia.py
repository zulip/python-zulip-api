#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from zulip_bots.test_lib import BotTestCase

class TestWikipediaBot(BotTestCase):
    bot_name = "wikipedia"

    def test_bot(self):

        # Single-word query
        bot_response = "For search term \"happy\", https://en.wikipedia.org/wiki/Happiness"
        with self.mock_http_conversation('test_single_word'):
            self.assert_bot_response(
                message = {'content': 'happy'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # Multi-word query
        bot_response = "For search term \"The sky is blue\", https://en.wikipedia.org/wiki/Sky_blue"
        with self.mock_http_conversation('test_multi_word'):
            self.assert_bot_response(
                message = {'content': 'The sky is blue'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # Number query
        bot_response = "For search term \"123\", https://en.wikipedia.org/wiki/123"
        with self.mock_http_conversation('test_number_query'):
            self.assert_bot_response(
                message = {'content': '123'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # Hash query
        bot_response = "For search term \"#\", https://en.wikipedia.org/wiki/Number_sign"
        with self.mock_http_conversation('test_hash_query'):
            self.assert_bot_response(
                message = {'content': '#'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # Incorrect word
        bot_response = "I am sorry. The search term you provided is not found :slightly_frowning_face:"
        with self.mock_http_conversation('test_incorrect_query'):
            self.assert_bot_response(
                message = {'content': 'sssssss kkkkk'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # Empty query, no request made to the Internet.
        bot_response = "Please enter your message after @mention-bot"
        self.assert_bot_response(
            message = {'content': ''},
            response = {'content': bot_response},
            expected_method='send_reply'
        )

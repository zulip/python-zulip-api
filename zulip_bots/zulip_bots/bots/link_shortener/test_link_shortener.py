#!/usr/bin/env python

from zulip_bots.test_lib import BotTestCase

class TestLinkShortenerBot(BotTestCase):
    bot_name = "link_shortener"

    def test_bot(self) -> None:
        MESSAGE = 'Shorten https://www.github.com/zulip/zulip please.'
        RESPONSE = 'https://www.github.com/zulip/zulip: https://goo.gl/6uoWKb'

        with self.mock_config_info({'key': 'qwertyuiop'}), \
                self.mock_http_conversation('test_normal'):
            self.initialize_bot()

            self.assert_bot_response(
                message = {'content': MESSAGE},
                response = {'content': RESPONSE},
                expected_method='send_reply'
            )

    def test_bot_empty(self) -> None:
        MESSAGE = 'Shorten nothing please.'
        RESPONSE = 'No links found. Send "help" to see usage instructions.'

        # No `mock_http_conversation` is necessary because the bot will
        # recognize that no links are in the message and won't make any HTTP
        # requests.
        with self.mock_config_info({'key': 'qwertyuiop'}):
            self.initialize_bot()

            self.assert_bot_response(
                message = {'content': MESSAGE},
                response = {'content': RESPONSE},
                expected_method='send_reply'
            )

    def test_bot_help(self) -> None:
        MESSAGE = 'help'
        RESPONSE = (
            'Mention the link shortener bot in a conversation and then enter '
            'any URLs you want to shorten in the body of the message.'
        )

        # No `mock_http_conversation` is necessary because the bot will
        # recognize that the message is 'help' and won't make any HTTP
        # requests.
        with self.mock_config_info({'key': 'qwertyuiop'}):
            self.initialize_bot()

            self.assert_bot_response(
                message = {'content': MESSAGE},
                response = {'content': RESPONSE},
                expected_method='send_reply'
            )

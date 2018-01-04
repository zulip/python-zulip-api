from unittest.mock import patch
from zulip_bots.test_lib import BotTestCase

class TestLinkShortenerBot(BotTestCase):
    bot_name = "link_shortener"

    def _test(self, message: str, response: str) -> None:
        with self.mock_config_info({'key': 'qwertyuiop'}):
            self.verify_reply(message, response)

    def test_bot_responds_to_empty_message(self) -> None:
        with patch('requests.post'):
            self._test('', 'No links found. Send "help" to see usage instructions.')

    def test_normal(self) -> None:
        with self.mock_http_conversation('test_normal'):
            self._test('Shorten https://www.github.com/zulip/zulip please.',
                       'https://www.github.com/zulip/zulip: https://goo.gl/6uoWKb')

    def test_no_links(self) -> None:
        # No `mock_http_conversation` is necessary because the bot will
        # recognize that no links are in the message and won't make any HTTP
        # requests.
        with patch('requests.post'):
            self._test('Shorten nothing please.',
                       'No links found. Send "help" to see usage instructions.')

    def test_help(self) -> None:
        # No `mock_http_conversation` is necessary because the bot will
        # recognize that the message is 'help' and won't make any HTTP
        # requests.
        with patch('requests.post'):
            self._test('help',
                       ('Mention the link shortener bot in a conversation and then '
                        'enter any URLs you want to shorten in the body of the message.'))

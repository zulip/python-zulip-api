from zulip_bots.test_lib import StubBotTestCase

class TestLinkShortenerBot(StubBotTestCase):
    bot_name = "link_shortener"

    def _test(self, message, response):
        with self.mock_config_info({'key': 'qwertyuiop'}):
            self.verify_reply(message, response)

    def test_bot(self):
        message = 'Shorten https://www.github.com/zulip/zulip please.'
        response = 'https://www.github.com/zulip/zulip: https://goo.gl/6uoWKb'

        with self.mock_http_conversation('test_normal'):
            self._test(message, response)

    def test_bot_empty(self):
        message = 'Shorten nothing please.'
        response = 'No links found. Send "help" to see usage instructions.'

        # No `mock_http_conversation` is necessary because the bot will
        # recognize that no links are in the message and won't make any HTTP
        # requests.
        self._test(message, response)

    def test_bot_help(self):
        message = 'help'
        response = ('Mention the link shortener bot in a conversation and then '
                    'enter any URLs you want to shorten in the body of the message.')

        # No `mock_http_conversation` is necessary because the bot will
        # recognize that the message is 'help' and won't make any HTTP
        # requests.
        self._test(message, response)

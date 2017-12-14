from zulip_bots.test_lib import BotTestCase

from unittest.mock import patch

class TestGoogleSearchBot(BotTestCase):
    bot_name = 'google_search'

    # Simple query
    def test_normal(self) -> None:
        with self.mock_http_conversation('test_normal'):
            self.verify_reply(
                'zulip',
                'Found Result: [Zulip](https://www.google.com/url?url=https%3A%2F%2Fzulipchat.com%2F)'
            )

    def test_bot_help(self) -> None:
        help_message = "To use this bot, start messages with @mentioned-bot, \
                    followed by what you want to search for. If \
                    found, Zulip will return the first search result \
                    on Google.\
                    \
                    An example message that could be sent is:\
                    '@mentioned-bot zulip' or \
                    '@mentioned-bot how to create a chatbot'."
        self.verify_reply('', help_message)
        self.verify_reply('help', help_message)

    def test_bot_no_results(self) -> None:
        with self.mock_http_conversation('test_no_result'):
            self.verify_reply('no res', 'Found no results.')

    def test_attribute_error(self) -> None:
        with self.mock_http_conversation('test_attribute_error'), \
                patch('logging.exception'):
            self.verify_reply('test', 'Error: Search failed. \'NoneType\' object has no attribute \'findAll\'.')

    # Makes sure cached results, irrelevant links, or empty results are not displayed
    def test_ignore_links(self) -> None:
        with self.mock_http_conversation('test_ignore_links'):
            # The bot should ignore all links, apart from the zulip link at the end (googlesearch.py lines 23-38)
            # Then it should send the zulip link
            # See test_ignore_links.json
            self.verify_reply(
                'zulip',
                'Found Result: [Zulip](https://www.google.com/url?url=https%3A%2F%2Fzulipchat.com%2F)'
            )

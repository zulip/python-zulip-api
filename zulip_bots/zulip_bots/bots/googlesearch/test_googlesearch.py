#!/usr/bin/env python

from zulip_bots.test_lib import StubBotTestCase

from typing import Any

class TestGoogleSearchBot(StubBotTestCase):
    bot_name = 'googlesearch'

    # Simple query
    def test_normal(self: Any) -> None:
        with self.mock_http_conversation('test_normal'):
            self.verify_reply(
                'zulip',
                'Found Result: [Zulip](https://www.google.com/url?url=https%3A%2F%2Fzulipchat.com%2F)'
            )

    def test_bot_help(self: Any) -> None:
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

    def test_bot_no_results(self: Any) -> None:
        with self.mock_http_conversation('test_no_result'):
            self.verify_reply('no res', 'Found no results.')

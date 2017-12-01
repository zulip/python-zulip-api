#!/usr/bin/env python

from zulip_bots.test_lib import StubBotTestCase

class TestWikipediaBot(StubBotTestCase):
    bot_name = "wikipedia"

    def test_bot(self):

        # Single-word query
        bot_request = 'happy'
        bot_response = "For search term \"happy\", https://en.wikipedia.org/wiki/Happiness"
        with self.mock_http_conversation('test_single_word'):
            self.verify_reply(bot_request, bot_response)

        # Multi-word query
        bot_request = 'The sky is blue'
        bot_response = "For search term \"The sky is blue\", https://en.wikipedia.org/wiki/Sky_blue"
        with self.mock_http_conversation('test_multi_word'):
            self.verify_reply(bot_request, bot_response)

        # Number query
        bot_request = '123'
        bot_response = "For search term \"123\", https://en.wikipedia.org/wiki/123"
        with self.mock_http_conversation('test_number_query'):
            self.verify_reply(bot_request, bot_response)

        # Hash query
        bot_request = '#'
        bot_response = "For search term \"#\", https://en.wikipedia.org/wiki/Number_sign"
        with self.mock_http_conversation('test_hash_query'):
            self.verify_reply(bot_request, bot_response)

        # Incorrect word
        bot_request = 'sssssss kkkkk'
        bot_response = "I am sorry. The search term you provided is not found :slightly_frowning_face:"
        with self.mock_http_conversation('test_incorrect_query'):
            self.verify_reply(bot_request, bot_response)

        # Empty query, no request made to the Internet.
        bot_request = ''
        bot_response = "Please enter your message after @mention-bot"
        self.verify_reply(bot_request, bot_response)

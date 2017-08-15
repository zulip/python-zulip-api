#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import json

from zulip_bots.test_lib import BotTestCase

class TestYodaBot(BotTestCase):
    bot_name = "yoda"

    def test_bot(self):

        # Test normal sentence (1).
        bot_response = "Learn how to speak like me someday, you will. Yes, hmmm."

        with self.mock_config_info({'api_key': '12345678'}), \
                self.mock_http_conversation('test_1'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': 'You will learn how to speak like me someday.'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # Test normal sentence (2).
        bot_response = "Much to learn, you still have."

        with self.mock_config_info({'api_key': '12345678'}), \
                self.mock_http_conversation('test_2'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': 'you still have much to learn'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # Test only numbers.
        bot_response = "23456.  Herh herh herh."

        with self.mock_config_info({'api_key': '12345678'}), \
                self.mock_http_conversation('test_only_numbers'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': '23456'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # Test help.
        bot_response = '''
            This bot allows users to translate a sentence into
            'Yoda speak'.
            Users should preface messages with '@mention-bot'.

            Before running this, make sure to get a Mashape Api token.
            Instructions are in the 'readme.md' file.
            Store it in the 'yoda.conf' file.
            The 'yoda.conf' file should be located in this bot's (zulip_bots/bots/yoda/yoda)
            directory.
            Example input:
            @mention-bot You will learn how to speak like me someday.
            '''
        self.assert_bot_response(
            message = {'content': 'help'},
            response = {'content': bot_response},
            expected_method='send_reply'
        )

        # Test empty message.
        bot_response = '''
            This bot allows users to translate a sentence into
            'Yoda speak'.
            Users should preface messages with '@mention-bot'.

            Before running this, make sure to get a Mashape Api token.
            Instructions are in the 'readme.md' file.
            Store it in the 'yoda.conf' file.
            The 'yoda.conf' file should be located in this bot's (zulip_bots/bots/yoda/yoda)
            directory.
            Example input:
            @mention-bot You will learn how to speak like me someday.
            '''
        self.assert_bot_response(
            message = {'content': ''},
            response = {'content': bot_response},
            expected_method='send_reply'
        )

        # Test invalid input.
        bot_response = "Invalid input, please check the sentence you have entered."
        with self.mock_config_info({'api_key': '12345678'}), \
                self.mock_http_conversation('test_invalid_input'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': '@#$%^&*'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

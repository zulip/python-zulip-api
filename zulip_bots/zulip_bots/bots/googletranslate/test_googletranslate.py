#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import json

from unittest.mock import patch
from requests.exceptions import HTTPError, ConnectionError

from zulip_bots.test_lib import BotTestCase
from zulip_bots.bots.googletranslate.googletranslate import TranslateError

help_text = '''
Google translate bot
Please format your message like:
`@-mention "<text_to_translate>" <target-language> <source-language(optional)>`
Visit [here](https://cloud.google.com/translate/docs/languages) for all languages
'''

class TestGoogleTranslateBot(BotTestCase):
    bot_name = "googletranslate"

    def test_normal(self):
        with self.mock_config_info({'key': 'abcdefg'}), \
                self.mock_http_conversation('test_normal'):
                    with self.mock_http_conversation('test_languages'):
                        self.initialize_bot()
                    self.assert_bot_response(
                        message = {'content': '"hello" de', 'sender_full_name': 'tester'},
                        response = {'content': 'Hallo (from tester)'},
                        expected_method = 'send_reply'
                    )

    def test_source_language_not_found(self):
        with self.mock_config_info({'key': 'abcdefg'}), \
                self.mock_http_conversation('test_languages'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': '"hello" german foo', 'sender_full_name': 'tester'},
                response = {'content': 'Source language not found. Visit [here](https://cloud.google.com/translate/docs/languages) for all languages'},
                expected_method = 'send_reply'
            )

    def test_target_language_not_found(self):
        with self.mock_config_info({'key': 'abcdefg'}), \
                self.mock_http_conversation('test_languages'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': '"hello" bar english', 'sender_full_name': 'tester'},
                response = {'content': 'Target language not found. Visit [here](https://cloud.google.com/translate/docs/languages) for all languages'},
                expected_method = 'send_reply'
            )

    def test_403(self):
        with self.mock_config_info({'key': 'abcdefg'}), \
                self.mock_http_conversation('test_403'):
                    with self.mock_http_conversation('test_languages'):
                        self.initialize_bot()
                    self.assert_bot_response(
                        message = {'content': '"hello" german english', 'sender_full_name': 'tester'},
                        response = {'content': 'Translate Error. Invalid API Key..'},
                        expected_method = 'send_reply'
                    )

    def test_help_empty(self):
        with self.mock_config_info({'key': 'abcdefg'}), \
                self.mock_http_conversation('test_languages'):
            self.initialize_bot()
        self.assert_bot_response(
            message = {'content': '', 'sender_full_name': 'tester'},
            response = {'content': help_text},
            expected_method = 'send_reply'
        )

    def test_help_command(self):
        with self.mock_config_info({'key': 'abcdefg'}), \
                self.mock_http_conversation('test_languages'):
            self.initialize_bot()
        self.assert_bot_response(
            message = {'content': 'help', 'sender_full_name': 'tester'},
            response = {'content': help_text},
            expected_method = 'send_reply'
        )

    def test_help_too_many_args(self):
        with self.mock_config_info({'key': 'abcdefg'}), \
                self.mock_http_conversation('test_languages'):
            self.initialize_bot()
        self.assert_bot_response(
            message = {'content': '"hello" de english foo bar', 'sender_full_name': 'tester'},
            response = {'content': help_text},
            expected_method = 'send_reply'
        )

    def test_help_no_langs(self):
        with self.mock_config_info({'key': 'abcdefg'}), \
                self.mock_http_conversation('test_languages'):
            self.initialize_bot()
        self.assert_bot_response(
            message = {'content': '"hello"', 'sender_full_name': 'tester'},
            response = {'content': help_text},
            expected_method = 'send_reply'
        )

    def test_quotation_in_text(self):
        with self.mock_config_info({'key': 'abcdefg'}), \
                self.mock_http_conversation('test_quotation'):
                    with self.mock_http_conversation('test_languages'):
                        self.initialize_bot()
                    self.assert_bot_response(
                        message = {'content': '"this has "quotation" marks in" english', 'sender_full_name': 'tester'},
                        response = {'content': 'this has "quotation" marks in (from tester)'},
                        expected_method = 'send_reply'
                    )

    def test_exception(self):
        with self.mock_config_info({'key': 'abcdefg'}), \
                patch('zulip_bots.bots.googletranslate.googletranslate.translate', side_effect=Exception):
                    with self.mock_http_conversation('test_languages'):
                        self.initialize_bot()
                    self.assertRaises(Exception)
                    self.assert_bot_response(
                        message = {'content': '"hello" de', 'sender_full_name': 'tester'},
                        response = {'content': 'Error. .'},
                        expected_method = 'send_reply'
                    )

    def test_get_language_403(self):
        with self.mock_config_info({'key': 'abcdefg'}), \
                self.mock_http_conversation('test_language_403'), \
                self.assertRaises(TranslateError):
                        self.initialize_bot()

    def test_connection_error(self):
        with self.mock_config_info({'key': 'abcdefg'}), \
                patch('requests.post', side_effect=ConnectionError()), \
                patch('logging.warning'):
                    with self.mock_http_conversation('test_languages'):
                        self.initialize_bot()
                    self.assert_bot_response(
                        message = {'content': '"test" en', 'sender_full_name': 'tester'},
                        response = {'content': 'Could not connect to Google Translate. .'},
                        expected_method = 'send_reply'
                    )

#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from zulip_bots.test_lib import BotTestCase

class TestFollowUpBot(BotTestCase):
    bot_name = "followup"
    mock_config_default_stream = {'stream': 'followup'}
    mock_config_specified_stream = {'stream': 'issue'}

    def test_bot_default_stream(self):
        expected_send_reply = [
            ("", 'Please specify the message you want to send to followup stream after @mention-bot')
        ]
        self.check_expected_responses(expected_send_reply, expected_method='send_reply')

        expected_send_message = [
            ("foo",
             {'type': 'stream',
              'to': 'followup',
              'subject': 'foo_sender@zulip.com',
              'content': 'from foo_sender@zulip.com: foo'}),
            ("I have completed my task in default stream",
             {'type': 'stream',
              'to': 'followup',
              'subject': 'foo_sender@zulip.com',
              'content': 'from foo_sender@zulip.com: I have completed my task in default stream'}),
        ]

        with self.mock_config_info(self.mock_config_default_stream):
            self.initialize_bot()
            self.check_expected_responses(expected_send_message, expected_method='send_message')

    def test_bot_specified_stream(self):
        expected_send_reply = [
            ("", 'Please specify the message you want to send to followup stream after @mention-bot')
        ]
        self.check_expected_responses(expected_send_reply, expected_method='send_reply')

        expected_send_message = [
            ("foo",
             {'type': 'stream',
              'to': 'issue',
              'subject': 'foo_sender@zulip.com',
              'content': 'from foo_sender@zulip.com: foo'}),
            ("I have completed my task in specified stream",
             {'type': 'stream',
              'to': 'issue',
              'subject': 'foo_sender@zulip.com',
              'content': 'from foo_sender@zulip.com: I have completed my task in specified stream'}),
        ]
        with self.mock_config_info(self.mock_config_specified_stream):
            self.initialize_bot()
            self.check_expected_responses(expected_send_message, expected_method='send_message')

#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from six.moves import zip

from zulip_bots.test_lib import BotTestCase

class TestMessageInfoBot(BotTestCase):
    bot_name = "message_info"

    def test_bot(self):
        message = "This should be five words."
        response = {
            'type': 'private',
            'to': 'foo_sender@zulip.com',
            'content': 'You sent a message with 5 words.',
        }
        expected_conversation = [
            (message, response)
        ]
        self.check_expected_responses(
            expected_conversation,
            expected_method='send_message',
        )

#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from zulip_bots.test_lib import BotTestCase
from zulip_bots.lib import StateHandler


class TestIncrementorBot(BotTestCase):
    bot_name = "incrementor"

    def test_bot(self):
        self.initialize_bot()
        messages = [  # Template for message inputs to test, absent of message content
            {
                'type': 'stream',
                'display_recipient': 'some stream',
                'subject': 'some subject',
                'sender_email': 'foo_sender@zulip.com',
            },
            {
                'type': 'private',
                'sender_email': 'foo_sender@zulip.com',
            },
        ]
        self.assert_bot_response(dict(messages[0], content=""), {'content': "1"},
                                 'send_reply')
        # Last test commented out since we don't have update_message
        # support in the test framework yet.

        # self.assert_bot_response(dict(messages[0], content=""), {'message_id': 5, 'content': "2"},
        #                          'update_message', storage)

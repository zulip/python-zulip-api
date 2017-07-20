#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from zulip_bots.test_lib import BotTestCase

class TestFollowUpBot(BotTestCase):
    bot_name = "followup"

    def test_bot(self):
        self.check_expected_responses(expected_method='send_reply', test_file_name='test_send_reply')

        self.check_expected_responses(expected_method='send_message', test_file_name='test_send_message')

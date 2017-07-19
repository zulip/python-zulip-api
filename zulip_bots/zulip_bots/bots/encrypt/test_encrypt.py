#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from zulip_bots.test_lib import BotTestCase

class TestEncryptBot(BotTestCase):
    bot_name = "encrypt"

    def test_bot(self):
        self.check_expected_responses(test_file_name='test_1')

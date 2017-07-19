#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import mock
from zulip_bots.test_lib import BotTestCase

class TestXkcdBot(BotTestCase):
    bot_name = "xkcd"

    @mock.patch('logging.exception')
    def test_bot(self, mock_logging_exception):
        self.check_expected_responses(test_file_name='test_1')

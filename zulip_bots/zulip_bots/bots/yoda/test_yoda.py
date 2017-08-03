#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import json

from zulip_bots.test_lib import BotTestCase

class TestYodaBot(BotTestCase):
    bot_name = "yoda"

    def test_bot(self):
        bot_response = "Learn how to speak like me someday, you will. Yes, hmmm."

        with self.mock_config_info({'api_key': '12345678'}), \
                self.mock_http_conversation('test_1'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': 'You will learn how to speak like me someday.'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

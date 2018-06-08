"""
Most of the testing for the actual game are done in test_database

This is only to really verify the output of the chat
"""

from unittest import mock

import zulip_bots.bots.merels.merels
import zulip_bots.test_lib


class TestFollowUpBot(zulip_bots.test_lib.BotTestCase, DefaultTests):
    bot_name = "merels"

    def test_no_command(self):
        message = dict(
            content='magic',
            type='stream',
            sender_email="boo@email.com",
            sender_full_name="boo"
        )

        res = self.get_response(message)

        self.assertEqual(res['content'],
                         'You are not in a game at the moment.'
                         ' Type `help` for help.')

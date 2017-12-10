#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from zulip_bots.test_lib import (
    StubBotHandler,
    StubBotTestCase,
    get_bot_message_handler,
)

from typing import Any


class TestFollowUpBot(StubBotTestCase):
    bot_name = "followup"

    def test_no_text(self) -> None:
        bot_response = 'Please specify the message you want to send to followup stream after @mention-bot'

        with self.mock_config_info({'stream': 'followup'}):
            self.verify_reply('', bot_response)

    def test_help_text(self) -> None:
        request = 'help'
        bot_response = '''
            This plugin will allow users to flag messages
            as being follow-up items.  Users should preface
            messages with "@mention-bot".

            Before running this, make sure to create a stream
            called "followup" that your API user can send to.
            '''

        with self.mock_config_info({'stream': 'followup'}):
            self.verify_reply(request, bot_response)

    def test_followup_stream(self) -> None:
        message = dict(
            content='foo',
            type='stream',
            sender_email='foo@example.com',
        )
        with self.mock_config_info({'stream': 'followup'}):
            response = self.get_response(message)
        self.assertEqual(response['content'], 'from foo@example.com: foo')
        self.assertEqual(response['to'], 'followup')

    def test_different_stream(self) -> None:
        message = dict(
            content='foo',
            type='stream',
            sender_email='foo@example.com',
        )
        with self.mock_config_info({'stream': 'issue'}):
            response = self.get_response(message)
        self.assertEqual(response['content'], 'from foo@example.com: foo')
        self.assertEqual(response['to'], 'issue')

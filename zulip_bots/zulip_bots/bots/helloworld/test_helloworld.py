#!/usr/bin/env python

from zulip_bots.test_lib import StubBotTestCase

class TestHelpBot(StubBotTestCase):
    bot_name = "helloworld"  # type: str

    def test_bot(self) -> None:
        dialog = [
            ('', 'beep boop'),
            ('help', 'beep boop'),
            ('foo', 'beep boop'),
        ]

        self.verify_dialog(dialog)

#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from six.moves import zip

from zulip_bots.test_lib import BotTestCase

class TestHelloWorldDefaultsBot(BotTestCase):
    bot_name = "helloworld_defaults"

    def test_bot(self):

        # Check for some possible inputs, which should all be responded to with txt
        txt = "beep boop"
        beep_messages = ["foo", "Hi, my name is abc"]
        self.check_expected_responses(list(zip(beep_messages, len(beep_messages)*[txt])))

        self.check_expected_responses([("hello", "Hello!")])

        # Don't check for these, as they are handled by default in the library
#        ""
#        "about"
#        "commands"
#        "help"

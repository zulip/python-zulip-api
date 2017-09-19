#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from zulip_bots.test_lib import BotTestCase

class TestDefineBot(BotTestCase):
    bot_name = "define"

    def test_bot(self):

        # Only one type(noun) of word.
        bot_response = ("**cat**:\n\n* (**noun**) a small domesticated carnivorous mammal "
                        "with soft fur, a short snout, and retractile claws. It is widely "
                        "kept as a pet or for catching mice, and many breeds have been "
                        "developed.\n&nbsp;&nbsp;their pet cat\n\n")
        with self.mock_http_conversation('test_single_type_word'):
            self.assert_bot_response(
                message = {'content': 'cat'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # Multi-type word.
        bot_response = ("**help**:\n\n"
                        "* (**verb**) make it easier or possible for (someone) to do something by offering them one's services or resources.\n"
                        "&nbsp;&nbsp;they helped her with domestic chores\n\n\n"
                        "* (**verb**) serve someone with (food or drink).\n"
                        "&nbsp;&nbsp;may I help you to some more meat?\n\n\n"
                        "* (**verb**) cannot or could not avoid.\n"
                        "&nbsp;&nbsp;he couldn't help laughing\n\n\n"
                        "* (**noun**) the action of helping someone to do something.\n"
                        "&nbsp;&nbsp;I asked for help from my neighbours\n\n\n"
                        "* (**exclamation**) used as an appeal for urgent assistance.\n"
                        "&nbsp;&nbsp;Help! I'm drowning!\n\n")
        with self.mock_http_conversation('test_multi_type_word'):
            self.assert_bot_response(
                message = {'content': 'help'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # Incorrect word.
        bot_response = "**foo**:\nCould not load definition."
        with self.mock_http_conversation('test_incorrect_word'):
            self.assert_bot_response(
                message = {'content': 'foo'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # Phrases are not defined. No request is sent to the Internet.
        bot_response = "Definitions for phrases are not available."
        self.assert_bot_response(
            message = {'content': 'The sky is blue'},
            response = {'content': bot_response},
            expected_method='send_reply'
        )

        # Symbols are considered invalid for words
        bot_response = "Definitions of words with symbols are not possible."
        self.assert_bot_response(
            message = {'content': '#'},
            response = {'content': bot_response},
            expected_method='send_reply'
        )

        # Empty messages are returned with a prompt to reply. No request is sent to the Internet.
        bot_response = "Please enter a word to define."
        self.assert_bot_response(
            message = {'content': ''},
            response = {'content': bot_response},
            expected_method='send_reply'
        )

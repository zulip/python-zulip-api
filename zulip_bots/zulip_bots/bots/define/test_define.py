from zulip_bots.test_lib import BotTestCase, DefaultTests
from unittest.mock import patch

class TestDefineBot(BotTestCase, DefaultTests):
    bot_name = "define"

    def test_bot(self) -> None:

        # Only one type(noun) of word.
        bot_response = ("**cat**:\n\n* (**noun**) a small domesticated carnivorous mammal "
                        "with soft fur, a short snout, and retractile claws. It is widely "
                        "kept as a pet or for catching mice, and many breeds have been "
                        "developed.\n&nbsp;&nbsp;their pet cat\n\n")
        with self.mock_http_conversation('test_single_type_word'):
            self.verify_reply('cat', bot_response)

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
            self.verify_reply('help', bot_response)

        # Incorrect word.
        bot_response = "**foo**:\nCould not load definition."
        with self.mock_http_conversation('test_incorrect_word'):
            self.verify_reply('foo', bot_response)

        # Phrases are not defined. No request is sent to the Internet.
        bot_response = "Definitions for phrases are not available."
        self.verify_reply('The sky is blue', bot_response)

        # Symbols are considered invalid for words
        bot_response = "Definitions of words with symbols are not possible."
        self.verify_reply('#', bot_response)

        # Empty messages are returned with a prompt to reply. No request is sent to the Internet.
        bot_response = "Please enter a word to define."
        self.verify_reply('', bot_response)

    def test_connection_error(self) -> None:
        with patch('requests.get', side_effect=Exception), \
                patch('logging.exception'):
            self.verify_reply(
                'aeroplane',
                '**aeroplane**:\nCould not load definition.')

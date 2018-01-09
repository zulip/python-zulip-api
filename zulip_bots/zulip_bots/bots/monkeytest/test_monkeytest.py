

from zulip_bots.test_lib import BotTestCase


class MonkeyTestBot(BotTestCase):
    bot_name = "monkeytest"

    def test_normal(self):
        bot_response = "Test for http://www.google.com\nhttps://monkeytest.it/test/qwerty123"


        with self.mock_config_info({'key': '12345'}), \
             self.mock_http_conversation('test_bot'):
            self.verify_reply('google.com', bot_response)
    def test_help(self):
        self.verify_reply('help',"This is bot for Monkeytest.it(site for testing sites)\nWrite me adress of site you want to test")
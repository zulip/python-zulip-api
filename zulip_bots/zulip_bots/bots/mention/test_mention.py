from zulip_bots.bots.mention.mention import MentionHandler
from zulip_bots.test_lib import BotTestCase

class TestMentionBot(BotTestCase):
    bot_name = "mention"

    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info({'access_token': '12345'}):
            self.verify_reply('', 'Empty Mention Query')

    def test_help_query(self) -> None:
        with self.mock_config_info({'access_token': '12345'}):
            self.verify_reply('help', '''
        This is a Mention API Bot which will find mentions
        of the given keyword throughout the web.
        Version 1.00
        ''')

    def test_get_account_id(self) -> None:
        bot_test_instance = MentionHandler()
        bot_test_instance.access_token = 'TEST'

        with self.mock_http_conversation('get_account_id'):
            self.assertEqual(bot_test_instance.get_account_id(), 'TEST')

    def test_get_alert_id(self) -> None:
        bot_test_instance = MentionHandler()
        bot_test_instance.access_token = 'TEST'
        bot_test_instance.account_id = 'TEST'

        with self.mock_http_conversation('get_alert_id'):
            self.assertEqual(bot_test_instance.get_alert_id('TEST'), 'TEST')

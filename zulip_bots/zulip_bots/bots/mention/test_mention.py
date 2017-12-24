from zulip_bots.test_lib import BotTestCase

class TestMentionBot(BotTestCase):
    bot_name = "mention"

    def test_bot_responds_to_empty_message(self) -> None:
        # Offline query.
        with self.mock_config_info({'access_token': '12345'}):
            self.verify_reply('', 'Empty Mention Query')

    def test_help_query(self) -> None:
        # Offline query.
        with self.mock_config_info({'access_token': '12345'}):
            self.verify_reply('help', '''
        This is a Mention API Bot which will find mentions
        of the given keyword throughout the web.
        Version 1.00
        ''')

        # Offline query.
        with self.mock_config_info({'access_token': '12345'}):
            self.verify_reply('hElp', '''
        This is a Mention API Bot which will find mentions
        of the given keyword throughout the web.
        Version 1.00
        ''')

        # Offline query.
        with self.mock_config_info({'access_token': '12345'}):
            self.verify_reply('HELP', '''
        This is a Mention API Bot which will find mentions
        of the given keyword throughout the web.
        Version 1.00
        ''')

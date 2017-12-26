from zulip_bots.test_lib import BotTestCase

class TestBaremetricsBot(BotTestCase):
    bot_name = "baremetrics"

    def test_bot_responds_to_empty_message(self) -> None:
        # Offline query.
        with self.mock_config_info({'api_key': 'lk_bszeiVWvcScrPXbGR0S1A'}):
            self.verify_reply('', 'No Command Specified')

    def test_help_query(self) -> None:
        # Offline query.
        with self.mock_config_info({'api_key': 'lk_bszeiVWvcScrPXbGR0S1A'}):
            self.verify_reply('help', '''
        This bot gives updates about customer behavior, financial performance, and analytics
        for an organization using the Baremetrics Api.\n
        Enter `list-commands` to show the list of available commands.
        Version 1.0
        ''')

        # Offline query.
        with self.mock_config_info({'api_key': 'lk_bszeiVWvcScrPXbGR0S1A'}):
            self.verify_reply('hElp', '''
        This bot gives updates about customer behavior, financial performance, and analytics
        for an organization using the Baremetrics Api.\n
        Enter `list-commands` to show the list of available commands.
        Version 1.0
        ''')

        # Offline query.
        with self.mock_config_info({'api_key': 'lk_bszeiVWvcScrPXbGR0S1A'}):
            self.verify_reply('HELP', '''
        This bot gives updates about customer behavior, financial performance, and analytics
        for an organization using the Baremetrics Api.\n
        Enter `list-commands` to show the list of available commands.
        Version 1.0
        ''')

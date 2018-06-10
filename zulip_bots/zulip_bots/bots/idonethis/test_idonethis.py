from unittest.mock import patch

from zulip_bots.test_lib import BotTestCase, DefaultTests

class TestIDoneThisBot(BotTestCase, DefaultTests):
    bot_name = "idonethis"  # type: str

    def test_create_entry_default_team(self) -> None:
        with self.mock_config_info({'api_key': '12345678', 'default_team': 'testing team 1'}), \
                self.mock_http_conversation('test_create_entry'), \
                self.mock_http_conversation('team_list'):
            self.verify_reply('i did something and something else',
                              'Great work :thumbs_up:. New entry `something and something else` created!')

    def test_create_entry_quoted_team(self) -> None:
        with self.mock_config_info({'api_key': '12345678', 'default_team': 'test_team_2'}), \
                self.mock_http_conversation('test_create_entry'), \
                self.mock_http_conversation('team_list'):
            self.verify_reply('i did something and something else "--team=testing team 1"',
                              'Great work :thumbs_up:. New entry `something and something else` created!')

    def test_create_entry_single_word_team(self) -> None:
        with self.mock_config_info({'api_key': '12345678', 'default_team': 'testing team 1'}), \
                self.mock_http_conversation('test_create_entry_team_2'), \
                self.mock_http_conversation('team_list'):
            self.verify_reply('i did something and something else --team=test_team_2',
                              'Great work :thumbs_up:. New entry `something and something else` created!')

    def test_bad_key(self) -> None:
        with self.mock_config_info({'api_key': '87654321', 'default_team': 'testing team 1'}), \
                self.mock_http_conversation('test_401'), \
                patch('zulip_bots.bots.idonethis.idonethis.api_noop'), \
                patch('logging.error'):
            self.verify_reply('list teams',
                              'I can\'t currently authenticate with idonethis. Can you check that your API key is correct? '
                              'For more information see my documentation.')

    def test_list_team(self) -> None:
        with self.mock_config_info({'api_key': '12345678', 'default_team': 'testing team 1'}), \
                self.mock_http_conversation('team_list'):
            self.verify_reply('list teams',
                              'Teams:\n * testing team 1\n * test_team_2')

    def test_show_team_no_team(self) -> None:
        with self.mock_config_info({'api_key': '12345678', 'default_team': 'testing team 1'}), \
                self.mock_http_conversation('api_noop'):
            self.verify_reply('team info',
                              'Sorry, I don\'t understand what your trying to say. Use `@mention help` to see my help. '
                              'You must specify the team in which you request information from.')

    def test_show_team(self) -> None:
        with self.mock_config_info({'api_key': '12345678', 'default_team': 'testing team 1'}), \
                self.mock_http_conversation('test_show_team'), \
                patch('zulip_bots.bots.idonethis.idonethis.get_team_hash', return_value='31415926535') as get_team_hashFunction:
            self.verify_reply('team info testing team 1',
                              'Team Name: testing team 1\n'
                              'ID: `31415926535`\n'
                              'Created at: 2017-12-28T19:12:55.121+11:00')
            get_team_hashFunction.assert_called_with('testing team 1')

    def test_entries_list(self) -> None:
        with self.mock_config_info({'api_key': '12345678', 'default_team': 'testing team 1'}), \
                self.mock_http_conversation('test_entries_list'), \
                patch('zulip_bots.bots.idonethis.idonethis.get_team_hash', return_value='31415926535') as get_team_hashFunction:
            self.verify_reply('entries list testing team 1',
                              'Entries for testing team 1:\n'
                              ' * TESTING\n'
                              '  * Created at: 2018-01-04T21:10:13.084+11:00\n'
                              '  * Status: done\n'
                              '  * User: John Doe\n'
                              '  * Team: testing team 1\n'
                              '  * ID: 65e1b21fd8f63adede1daae0bdf28c0e47b84923\n'
                              ' * Grabbing some more data...\n'
                              '  * Created at: 2018-01-04T20:07:58.078+11:00\n'
                              '  * Status: done\n'
                              '  * User: John Doe\n'
                              '  * Team: testing team 1\n'
                              '  * ID: fa974ad8c1acb9e81361a051a697f9dae22908d6\n'
                              ' * GRABBING HTTP DATA\n'
                              '  * Created at: 2018-01-04T19:07:17.214+11:00\n'
                              '  * Status: done\n'
                              '  * User: John Doe\n'
                              '  * Team: testing team 1\n'
                              '  * ID: 72c8241d2218464433268c5abd6625ac104e3d8f')

    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info({'api_key': '12345678', 'bot_info': 'team'}), \
                self.mock_http_conversation('api_noop'):
            self.verify_reply('',
                              'Sorry, I don\'t understand what your trying to say. Use `@mention help` to see my help. '
                              'I can\'t understand the command you sent me :confused: ')

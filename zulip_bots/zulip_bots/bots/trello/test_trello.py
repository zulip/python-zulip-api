from unittest.mock import patch

from zulip_bots.bots.trello.trello import TrelloHandler
from zulip_bots.test_lib import BotTestCase
from zulip_bots.test_lib import StubBotHandler

mock_config = {
    'api_key': 'TEST',
    'access_token': 'TEST',
    'user_name': 'TEST'
}

class TestTrelloBot(BotTestCase):
    bot_name = "trello"  # type: str

    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info(mock_config), patch('requests.get'):
            self.verify_reply('', 'Empty Query')

    def test_bot_usage(self) -> None:
        with self.mock_config_info(mock_config), patch('requests.get'):
            self.verify_reply('help', '''
        This interactive bot can be used to interact with Trello.

        Use `list-commands` to get information about the supported commands.
        ''')

    def test_bot_quit_with_invalid_config(self) -> None:
        with self.mock_config_info(mock_config), self.assertRaises(StubBotHandler.BotQuitException):
            TrelloHandler().initialize(StubBotHandler())

    def test_invalid_command(self) -> None:
        with self.mock_config_info(mock_config), patch('requests.get'):
            self.verify_reply('abcd', 'Command not supported')

    def test_list_commands_command(self) -> None:
        expected_reply = ('**Commands:** \n'
                          '1. **help**: Get the bot usage information.\n'
                          '2. **list-commands**: Get information about the commands supported by the bot.\n'
                          '3. **get-all-boards**: Get all the boards under the configured account.\n'
                          '4. **get-all-cards <board_id>**: Get all the cards in the given board.\n'
                          '5. **get-all-checklists <card_id>**: Get all the checklists in the given card.\n'
                          '6. **get-all-lists <board_id>**: Get all the lists in the given board.\n')

        with self.mock_config_info(mock_config), patch('requests.get'):
            self.verify_reply('list-commands', expected_reply)

    def test_get_all_boards_command(self) -> None:
        with self.mock_config_info(mock_config), patch('requests.get'):
            with self.mock_http_conversation('get_all_boards'):
                self.verify_reply('get-all-boards', '**Boards:** \n')

            with self.mock_http_conversation('get_board_descs'):
                bot_instance = TrelloHandler()
                bot_instance.initialize(StubBotHandler)

                self.assertEqual(bot_instance.get_board_descs(['TEST']), '1.[TEST](TEST) (`TEST`)\n')

    def test_get_all_cards_command(self) -> None:
        with self.mock_config_info(mock_config), patch('requests.get'):
            with self.mock_http_conversation('get_cards'):
                self.verify_reply('get-all-cards TEST', '**Cards:** \n1. [TEST](TEST) (`TEST`)\n')

    def test_get_all_checklists_command(self) -> None:
        with self.mock_config_info(mock_config), patch('requests.get'):
            with self.mock_http_conversation('get_checklists'):
                self.verify_reply('get-all-checklists TEST', '**Checklists:** \n'
                                                             '1. `TEST`:\n'
                                                             ' * [X] TEST_1\n * [X] TEST_2\n'
                                                             ' * [-] TEST_3\n * [-] TEST_4\n')

    def test_get_all_lists_command(self) -> None:
        with self.mock_config_info(mock_config), patch('requests.get'):
            with self.mock_http_conversation('get_lists'):
                self.verify_reply('get-all-lists TEST', ('**Lists:** \n'
                                                         '1. TEST_A\n'
                                                         '  * TEST_1\n'
                                                         '2. TEST_B\n'
                                                         '  * TEST_2\n'))

    def test_command_exceptions(self) -> None:
        """Add appropriate tests here for all additional commands with try/except blocks.
        This ensures consistency."""

        expected_error_response = 'Invalid Response. Please check configuration and parameters.'

        with self.mock_config_info(mock_config), patch('requests.get'):
            with self.mock_http_conversation('exception_boards'):
                self.verify_reply('get-all-boards', expected_error_response)

            with self.mock_http_conversation('exception_cards'):
                self.verify_reply('get-all-cards TEST', expected_error_response)

            with self.mock_http_conversation('exception_checklists'):
                self.verify_reply('get-all-checklists TEST', expected_error_response)

            with self.mock_http_conversation('exception_lists'):
                self.verify_reply('get-all-lists TEST', expected_error_response)

    def test_command_invalid_arguments(self) -> None:
        """Add appropriate tests here for all additional commands with more than one arguments.
        This ensures consistency."""

        expected_error_response = 'Invalid Arguments.'

        with self.mock_config_info(mock_config), patch('requests.get'):
            self.verify_reply('get-all-cards', expected_error_response)
            self.verify_reply('get-all-checklists', expected_error_response)
            self.verify_reply('get-all-lists', expected_error_response)

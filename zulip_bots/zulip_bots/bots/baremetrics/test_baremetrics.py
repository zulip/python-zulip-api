from unittest.mock import patch
from zulip_bots.test_lib import BotTestCase
from zulip_bots.test_lib import StubBotHandler
from zulip_bots.bots.baremetrics.baremetrics import BaremetricsHandler

class TestBaremetricsBot(BotTestCase):
    bot_name = "baremetrics"

    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info({'api_key': 'TEST'}), \
                patch('requests.get'):
            self.verify_reply('', 'No Command Specified')

    def test_help_query(self) -> None:
        with self.mock_config_info({'api_key': 'TEST'}), \
                patch('requests.get'):
            self.verify_reply('help', '''
        This bot gives updates about customer behavior, financial performance, and analytics
        for an organization using the Baremetrics Api.\n
        Enter `list-commands` to show the list of available commands.
        Version 1.0
        ''')

    def test_list_commands_command(self) -> None:
        with self.mock_config_info({'api_key': 'TEST'}), \
                patch('requests.get'):
            self.verify_reply('list-commands', '**Available Commands:** \n'
                                               ' - help : Display bot info\n'
                                               ' - list-commands : Display the list of available commands\n'
                                               ' - account-info : Display the account info\n'
                                               ' - list-sources : List the sources\n'
                                               ' - list-plans <source_id> : List the plans for the source\n'
                                               ' - list-customers <source_id> : List the customers in the source\n'
                                               ' - list-subscriptions <source_id> : List the subscriptions in the '
                                               'source\n'
                                               ' - create-plan <source_id> <oid> <name> <currency> <amount> <interval> '
                                               '<interval_count> : Create a plan in the given source\n')

    def test_account_info_command(self) -> None:
        with self.mock_config_info({'api_key': 'TEST'}):
            with self.mock_http_conversation('account_info'):
                self.verify_reply('account-info', '**Your account information:** \nId: 376418\nCompany: NA\nDefault '
                                                  'Currency: United States Dollar')

    def test_list_sources_command(self) -> None:
        with self.mock_config_info({'api_key': 'TEST'}):
            with self.mock_http_conversation('list_sources'):
                self.verify_reply('list-sources', '**Listing sources:** \n1.ID: 5f7QC5NC0Ywgcu\nProvider: '
                                                  'baremetrics\nProvider ID: None\n\n')

    def test_list_plans_command(self) -> None:
        r = '**Listing plans:** \n1.Name: Plan 1\nActive: True\nInterval: year\nInterval Count: 1\nAmounts: \n' \
            ' - 450000 USD\n\n2.Name: Plan 2\nActive: True\nInterval: year\nInterval Count: 1\nAmounts: \n' \
            ' - 450000 USD\n\n'

        with self.mock_config_info({'api_key': 'TEST'}):
            with self.mock_http_conversation('list_plans'):
                self.verify_reply('list-plans TEST', r)

    def test_list_customers_command(self) -> None:
        r = '**Listing customers:** \n1.Name: Customer 1\nDisplay Name: Customer 1\nOID: customer_1\nActive: True\n' \
            'Email: customer_1@baremetrics.com\nNotes: Here are some notes\nCurrent Plans: \n - Plan 1\n\n'

        with self.mock_config_info({'api_key': 'TEST'}):
            with self.mock_http_conversation('list_customers'):
                self.verify_reply('list-customers TEST', r)

    def test_list_subscriptions_command(self) -> None:
        r = '**Listing subscriptions:** \n1.Customer Name: Customer 1\nCustomer Display Name: Customer 1\n' \
            'Customer OID: customer_1\nCustomer Email: customer_1@baremetrics.com\nActive: True\n' \
            'Plan Name: Plan 1\nPlan Amounts: \n - 1000 $\n\n'

        with self.mock_config_info({'api_key': 'TEST'}):
            with self.mock_http_conversation('list_subscriptions'):
                self.verify_reply('list-subscriptions TEST', r)

    def test_exception_when_api_key_is_invalid(self)-> None:
        bot_test_instance = BaremetricsHandler()

        with self.mock_config_info({'api_key': 'TEST'}):
            with self.mock_http_conversation('invalid_api_key'):
                with self.assertRaises(StubBotHandler.BotQuitException):
                    bot_test_instance.initialize(StubBotHandler())

    def test_invalid_command(self) -> None:
        with self.mock_config_info({'api_key': 'TEST'}), \
                patch('requests.get'):
            self.verify_reply('abcd', 'Invalid Command.')

    def test_missing_params(self) -> None:
        with self.mock_config_info({'api_key': 'TEST'}), \
                patch('requests.get'):
            self.verify_reply('list-plans', 'Missing Params.')

    def test_key_error(self) -> None:
        with self.mock_config_info({'api_key': 'TEST'}), \
                patch('requests.get'):
            with self.mock_http_conversation('test_key_error'):
                self.verify_reply('list-plans TEST', 'Invalid Response From API.')

    def test_create_plan_command(self) -> None:
        with self.mock_config_info({'api_key': 'TEST'}), \
                patch('requests.get'):
            with self.mock_http_conversation('create_plan'):
                self.verify_reply('create-plan TEST 1 TEST USD 123 TEST 123', 'Plan Created.')

    def test_create_plan_error_command(self) -> None:
        with self.mock_config_info({'api_key': 'TEST'}), \
                patch('requests.get'):
            with self.mock_http_conversation('create_plan_error'):
                self.verify_reply('create-plan TEST 1 TEST USD 123 TEST 123', 'Invalid Arguments Error.')

    def test_create_plan_argnum_error_command(self) -> None:
        with self.mock_config_info({'api_key': 'TEST'}), \
                patch('requests.get'):
            self.verify_reply('create-plan alpha beta', 'Invalid number of arguments.')

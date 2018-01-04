from zulip_bots.test_lib import BotTestCase, StubBotHandler, read_bot_fixture_data
import simple_salesforce
from simple_salesforce.exceptions import SalesforceAuthenticationFailed
from contextlib import contextmanager
from unittest.mock import patch
from typing import Any, Dict
import logging


@contextmanager
def mock_salesforce_query(test_name: str, bot_name: str) -> Any:
    response_data = read_bot_fixture_data(bot_name, test_name)
    sf_response = response_data.get('response')

    with patch('simple_salesforce.api.Salesforce.query') as mock_query:
        mock_query.return_value = sf_response
        yield


@contextmanager
def mock_salesforce_auth(is_success: bool) -> Any:
    if is_success:
        with patch('simple_salesforce.api.Salesforce.__init__') as mock_sf_init:
            mock_sf_init.return_value = None
            yield
    else:
        with patch(
            'simple_salesforce.api.Salesforce.__init__',
            side_effect=SalesforceAuthenticationFailed(403, 'auth failed')
        ) as mock_sf_init:
            mock_sf_init.return_value = None
            yield


@contextmanager
def mock_salesforce_commands_types() -> Any:
    with patch('zulip_bots.bots.salesforce.utils.commands', mock_commands), \
            patch('zulip_bots.bots.salesforce.utils.object_types', mock_object_types):
        yield


mock_config = {
    'username': 'name@example.com',
    'password': 'foo',
    'security_token': 'abcdefg'
}

help_text = '''Salesforce bot
This bot can do simple salesforce query requests
**All commands must be @-mentioned to the bot.**
Commands:
**find contact <name> [arguments]**: finds contacts
**find top opportunities <amount> [arguments]**: finds opportunities

Arguments:
**-limit <num>**: the maximum number of entries sent (default: 5)
**-show**: show all the properties of each entry (default: false)

This bot can also show details about any Salesforce links sent to it.

Supported Object types:
These are the types of Salesforce object supported by this bot.
The bot cannot show the details of any other object types.
Table
Table
'''


def echo(arg: str, sf: Any, command: Dict[str, Any]) -> str:
    return arg


mock_commands = [
    {
        'commands': ['find contact'],
        'object': 'contact',
        'description': 'finds contacts',
        'template': 'find contact <name>',
    },
    {
        'commands': ['find top opportunities'],
        'object': 'opportunity',
        'query': 'SELECT {} FROM {} WHERE isClosed=false ORDER BY amount DESC LIMIT {}',
        'description': 'finds opportunities',
        'template': 'find top opportunities <amount>',
        'rank_output': True,
        'force_keys': ['Amount'],
        'exclude_keys': ['Status'],
        'show_all_keys': True
    },
    {
        'commands': ['echo'],
        'callback': echo
    }
]


mock_object_types = {
    'contact': {
        'fields': 'Id, Name, Phone',
        'table': 'Table'
    },
    'opportunity': {
        'fields': 'Id, Name, Amount, Status',
        'table': 'Table'
    }
}


class TestSalesforceBot(BotTestCase):
    bot_name = "salesforce"  # type: str

    def _test(self, test_name: str, message: str, response: str, auth_success: bool=True) -> None:
        with self.mock_config_info(mock_config), \
                mock_salesforce_auth(auth_success), \
                mock_salesforce_query(test_name, 'salesforce'), \
                mock_salesforce_commands_types():
            self.verify_reply(message, response)

    def _test_initialize(self, auth_success: bool=True) -> None:
        with self.mock_config_info(mock_config), \
                mock_salesforce_auth(auth_success), \
                mock_salesforce_commands_types():
            bot, bot_handler = self._get_handlers()

    def test_bot_responds_to_empty_message(self) -> None:
        self._test('test_one_result', '', help_text)

    def test_one_result(self) -> None:
        res = '''**[foo](https://login.salesforce.com/foo_id)**
>**Phone**: 020 1234 5678
'''
        self._test('test_one_result', 'find contact foo', res)

    def test_multiple_results(self) -> None:
        res = '**[foo](https://login.salesforce.com/foo_id)**\n**[bar](https://login.salesforce.com/bar_id)**\n'
        self._test('test_multiple_results', 'find contact foo', res)

    def test_arg_show(self) -> None:
        res = '''**[foo](https://login.salesforce.com/foo_id)**
>**Phone**: 020 1234 5678

**[bar](https://login.salesforce.com/bar_id)**
>**Phone**: 020 5678 1234

'''
        self._test('test_multiple_results', 'find contact foo -show', res)

    def test_no_results(self) -> None:
        self._test('test_no_results', 'find contact foo', 'No records found.')

    def test_rank_and_force_keys(self) -> None:
        res = '''1) **[foo](https://login.salesforce.com/foo_id)**
>**Amount**: 2

2) **[bar](https://login.salesforce.com/bar_id)**
>**Amount**: 1

'''
        self._test('test_top_opportunities', 'find top opportunities 2', res)

    def test_limit_arg(self) -> None:
        res = '''**[foo](https://login.salesforce.com/foo_id)**
>**Phone**: 020 1234 5678
'''
        with self.assertLogs(level='INFO') as log:
            self._test('test_one_result', 'find contact foo -limit 1', res)
            self.assertIn('INFO:root:Searching with limit 1', log.output)

    def test_help(self) -> None:
        self._test('test_one_result', 'help', help_text)
        self._test('test_one_result', 'foo bar baz', help_text)
        self._test('test_one_result', 'find contact',
                   'Usage: find contact <name> [arguments]')

    def test_bad_auth(self) -> None:
        with self.assertRaises(StubBotHandler.BotQuitException):
            self._test_initialize(auth_success=False)

    def test_callback(self) -> None:
        self._test('test_one_result', 'echo hello', 'hello')

    def test_link_normal(self) -> None:
        res = '''**[foo](https://login.salesforce.com/foo_id)**
>**Phone**: 020 1234 5678
'''
        self._test('test_one_result',
                   'https://login.salesforce.com/1c3e5g7i9k1m3o5q7s', res)

    def test_link_invalid(self) -> None:
        self._test('test_one_result',
                   'https://login.salesforce.com/foo/bar/1c3e5g7$i9k1m3o5q7',
                   'Invalid salesforce link')

    def test_link_no_results(self) -> None:
        res = 'No object found. Make sure it is of the supported types. Type `help` for more info.'
        self._test('test_no_results',
                   'https://login.salesforce.com/1c3e5g7i9k1m3o5q7s', res)

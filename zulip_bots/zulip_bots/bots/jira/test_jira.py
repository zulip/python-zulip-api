from unittest.mock import patch
from zulip_bots.test_lib import BotTestCase

class TestJiraBot(BotTestCase):
    bot_name = 'jira'

    MOCK_CONFIG_INFO = {
        'username': 'example@example.com',
        'password': 'qwerty!123',
        'domain': 'example.atlassian.net'
    }

    MOCK_GET_JSON = {
        'fields': {
            'creator': {'name': 'admin'},
            'description': 'description',
            'priority': {'name': 'Medium'},
            'project': {'name': 'Tests'},
            'issuetype': {'name': 'Task'},
            'status': {'name': 'To Do'},
            'summary': 'summary'
        }
    }

    MOCK_GET_RESPONSE = '''\
**Issue *[TEST-13](https://example.atlassian.net/browse/TEST-13)*: summary**

 - Type: *Task*
 - Description:
 > description
 - Creator: *admin*
 - Project: *Tests*
 - Priority: *Medium*
 - Status: *To Do*
'''

    MOCK_CREATE_JSON = {
        'key': 'TEST-16'
    }

    MOCK_CREATE_RESPONSE = 'Issue *TEST-16* is up! https://example.atlassian.net/browse/TEST-16'

    MOCK_EDIT_JSON = {}

    MOCK_EDIT_RESPONSE = 'Issue *TEST-16* was edited! https://example.atlassian.net/browse/TEST-16'

    MOCK_NOTHING_RESPONSE = 'Sorry, I don\'t understand that! Send me `help` for instructions.'

    def test_get(self) -> None:
        with patch('requests.get') as response, \
                self.mock_config_info(self.MOCK_CONFIG_INFO):
            response.return_value.text = 'text so that it isn\'t assumed to be an error'
            response.return_value.json = lambda: self.MOCK_GET_JSON

            self.verify_reply('get "TEST-13"', self.MOCK_GET_RESPONSE)

    def test_create(self) -> None:
        with patch('requests.post') as response, \
                self.mock_config_info(self.MOCK_CONFIG_INFO):
            response.return_value.text = 'text so that it isn\'t assumed to be an error'
            response.return_value.json = lambda: self.MOCK_CREATE_JSON

            self.verify_reply(
                'create issue "Testing" in project "TEST" with type "Task"',
                self.MOCK_CREATE_RESPONSE
            )

    def test_edit(self) -> None:
        with patch('requests.put') as response, \
                self.mock_config_info(self.MOCK_CONFIG_INFO):
            response.return_value.text = 'text so that it isn\'t assumed to be an error'
            response.return_value.json = lambda: self.MOCK_EDIT_JSON

            self.verify_reply(
                'edit issue "TEST-16" to use description "description"',
                self.MOCK_EDIT_RESPONSE
            )

    # This overrides the default one in `BotTestCase`.
    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO):
            self.verify_reply('', self.MOCK_NOTHING_RESPONSE)

    def test_no_command(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO):
            self.verify_reply('qwertyuiop', self.MOCK_NOTHING_RESPONSE)

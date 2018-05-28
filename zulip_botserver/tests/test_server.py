import mock
import os
from typing import Any, Dict
import unittest
from .server_test_lib import BotServerTestCase
import six
import json

from zulip_botserver import server
from zulip_botserver.input_parameters import parse_args


class BotServerTests(BotServerTestCase):
    class MockMessageHandler(object):
        def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
            assert message == {'key': "test message"}

    class MockLibModule(object):
        def handler_class(self) -> Any:
            return BotServerTests.MockMessageHandler()

    @mock.patch('zulip_bots.lib.ExternalBotHandler')
    def test_successful_request(self, mock_ExternalBotHandler: mock.Mock) -> None:
        available_bots = ['helloworld']
        bots_config = {
            'helloworld': {
                'email': 'helloworld-bot@zulip.com',
                'key': '123456789qwertyuiop',
                'site': 'http://localhost',
            }
        }
        self.assert_bot_server_response(available_bots=available_bots,
                                        bots_config=bots_config,
                                        message=dict(message={'content': "test message"},
                                                     bot_email='helloworld-bot@zulip.com'),
                                        check_success=True)

    @mock.patch('zulip_bots.lib.ExternalBotHandler')
    def test_successful_request_from_two_bots(self, mock_ExternalBotHandler: mock.Mock) -> None:
        available_bots = ['helloworld', 'help']
        bots_config = {
            'helloworld': {
                'email': 'helloworld-bot@zulip.com',
                'key': '123456789qwertyuiop',
                'site': 'http://localhost',
            },
            'help': {
                'email': 'help-bot@zulip.com',
                'key': '123456789qwertyuiop',
                'site': 'http://localhost',
            }
        }
        self.assert_bot_server_response(available_bots=available_bots,
                                        message=dict(message={'content': "test message"},
                                                     bot_email='helloworld-bot@zulip.com'),
                                        bots_config=bots_config,
                                        check_success=True)

    def test_bot_module_not_exists(self) -> None:
        self.assert_bot_server_response(available_bots=[],
                                        message=dict(message={'content': "test message"},
                                                     bot_email='nonexistent-bot@zulip.com'),
                                        check_success=False)

    @mock.patch('logging.error')
    @mock.patch('zulip_bots.lib.StateHandler')
    def test_wrong_bot_credentials(self, mock_StateHandler: mock.Mock, mock_LoggingError: mock.Mock) -> None:
        available_bots = ['nonexistent-bot']
        bots_config = {
            'nonexistent-bot': {
                'email': 'helloworld-bot@zulip.com',
                'key': '123456789qwertyuiop',
                'site': 'http://localhost',
            }
        }
        # TODO: The following passes mypy, though the six stubs don't match the
        # unittest ones, so we could file a mypy bug to improve this.
        six.assertRaisesRegex(self,
                              ImportError,
                              "Bot \"nonexistent-bot\" doesn't exists. Please "
                              "make sure you have set up the flaskbotrc file correctly.",
                              lambda: self.assert_bot_server_response(
                                  available_bots=available_bots,
                                  message=dict(message={'content': "test message"},
                                               bot_email='helloworld-bot@zulip.com'),
                                  bots_config=bots_config))

    @mock.patch('sys.argv', ['zulip-bot-server', '--config-file', '/foo/bar/baz.conf'])
    def test_argument_parsing_defaults(self) -> None:
        opts = parse_args()
        assert opts.config_file == '/foo/bar/baz.conf'
        assert opts.bot_name is None
        assert opts.bot_config_file is None
        assert opts.hostname == '127.0.0.1'
        assert opts.port == 5002

    def test_read_config_file(self) -> None:
        with self.assertRaises(IOError):
            server.read_config_file("nonexistentfile.conf")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bot_conf1 = server.read_config_file(os.path.join(current_dir, "test.conf"))
        expected_config1 = {
            'helloworld': {
                'email': 'helloworld-bot@zulip.com',
                'key': 'value',
                'site': 'http://localhost',
            },
            'giphy': {
                'email': 'giphy-bot@zulip.com',
                'key': 'value2',
                'site': 'http://localhost',
            }
        }
        assert json.dumps(bot_conf1, sort_keys=True) == json.dumps(expected_config1, sort_keys=True)
        bot_conf2 = server.read_config_file(os.path.join(current_dir, "test.conf"), "redefined_bot")
        expected_config2 = {
            'redefined_bot': {
                'email': 'helloworld-bot@zulip.com',
                'key': 'value',
                'site': 'http://localhost',
            }
        }
        assert json.dumps(bot_conf2, sort_keys=True) == json.dumps(expected_config2, sort_keys=True)


if __name__ == '__main__':
    unittest.main()

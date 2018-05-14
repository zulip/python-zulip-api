import mock
from typing import Any, Dict
import unittest
from .server_test_lib import BotServerTestCase
import six

class BotServerTests(BotServerTestCase):
    class MockMessageHandler(object):
        def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
            assert message == {'key': "test message"}

    class MockLibModule(object):
        def handler_class(self) -> Any:
            return BotServerTests.MockMessageHandler()

    @mock.patch('zulip_botserver.server.ExternalBotHandler')
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
                                        check_success=True)

    def test_bot_module_not_exists(self) -> None:
        self.assert_bot_server_response(available_bots=[],
                                        payload_url="/bots/not_supported_bot",
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
                              lambda: self.assert_bot_server_response(available_bots=available_bots,
                                                                      bots_config=bots_config))

if __name__ == '__main__':
    unittest.main()

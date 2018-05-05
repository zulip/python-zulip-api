import unittest

from typing import List, Dict, Any, Tuple, Optional, IO

from zulip_bots.custom_exceptions import (
    ConfigValidationError,
)

from zulip_bots.request_test_lib import (
    mock_http_conversation,
    mock_request_exception
)

from zulip_bots.simple_lib import (
    SimpleStorage,
    SimpleMessageServer,
)

from zulip_bots.test_file_utils import (
    get_bot_message_handler,
    read_bot_fixture_data,
)

from zulip_bots.lib import BotIdentity

class StubBotHandler:
    def __init__(self) -> None:
        self.storage = SimpleStorage()
        self.full_name = 'test-bot'
        self.email = 'test-bot@example.com'
        self.message_server = SimpleMessageServer()
        self.reset_transcript()

    def reset_transcript(self) -> None:
        self.transcript = []  # type: List[Tuple[str, Dict[str, Any]]]

    def identity(self) -> BotIdentity:
        return BotIdentity(self.full_name, self.email)

    def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        self.transcript.append(('send_message', message))
        return self.message_server.send(message)

    def send_reply(self, message: Dict[str, Any], response: str,
                   widget_content: Optional[str]=None) -> Dict[str, Any]:
        response_message = dict(
            content=response,
            widget_content=widget_content
        )
        self.transcript.append(('send_reply', response_message))
        return self.message_server.send(response_message)

    def update_message(self, message: Dict[str, Any]) -> None:
        self.message_server.update(message)

    def upload_file_from_path(self, file_path):
        # type: (str) -> Dict[str, Any]
        with open(file_path, 'rb') as file:
            return self.message_server.upload_file(file)

    def upload_file(self, file):
        # type: (IO[Any]) -> Dict[str, Any]
        return self.message_server.upload_file(file)

    class BotQuitException(Exception):
        pass

    def quit(self, message: str="") -> None:
        raise self.BotQuitException()

    def get_config_info(self, bot_name: str, optional: bool=False) -> Dict[str, Any]:
        return {}

    def unique_reply(self) -> Dict[str, Any]:
        responses = [
            message
            for (method, message)
            in self.transcript
            if method == 'send_reply'
        ]
        self.ensure_unique_response(responses)
        return responses[0]

    def unique_response(self) -> Dict[str, Any]:
        responses = [
            message
            for (method, message)
            in self.transcript
        ]
        self.ensure_unique_response(responses)
        return responses[0]

    def ensure_unique_response(self, responses: List[Dict[str, Any]]) -> None:
        if not responses:
            raise Exception('The bot is not responding for some reason.')
        if len(responses) > 1:
            raise Exception('The bot is giving too many responses for some reason.')


class DefaultTests:
    bot_name = ''

    def make_request_message(self, content: str) -> Dict[str, Any]:
        raise NotImplementedError()

    def get_response(self, message: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()

    def test_bot_usage(self) -> None:
        bot = get_bot_message_handler(self.bot_name)
        assert bot.usage() != ''

    def test_bot_responds_to_empty_message(self) -> None:
        message = self.make_request_message('')

        # get_response will fail if we don't respond at all
        response = self.get_response(message)

        # we also want a non-blank response
        assert len(response['content']) >= 1


class BotTestCase(unittest.TestCase):
    bot_name = ''

    def _get_handlers(self) -> Tuple[Any, StubBotHandler]:
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        if hasattr(bot, 'initialize'):
            bot.initialize(bot_handler)

        return bot, bot_handler

    def get_response(self, message):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        bot, bot_handler = self._get_handlers()
        bot_handler.reset_transcript()
        bot.handle_message(message, bot_handler)
        return bot_handler.unique_response()

    def make_request_message(self, content: str) -> Dict[str, Any]:
        """
        This is mostly used internally but
        tests can override this behavior by
        mocking/subclassing.
        """
        message = dict(
            display_recipient='foo_stream',
            sender_email='foo@example.com',
            sender_full_name='Foo Test User',
            sender_id='123',
            content=content,
        )
        return message

    def get_reply_dict(self, request: str) -> Dict[str, Any]:
        bot, bot_handler = self._get_handlers()
        message = self.make_request_message(request)
        bot_handler.reset_transcript()
        bot.handle_message(message, bot_handler)
        reply = bot_handler.unique_reply()
        return reply

    def verify_reply(self, request: str, response: str) -> None:
        reply = self.get_reply_dict(request)
        self.assertEqual(response, reply['content'])

    def verify_dialog(self, conversation: List[Tuple[str, str]]) -> None:
        # Start a new message handler for the full conversation.
        bot, bot_handler = self._get_handlers()

        for (request, expected_response) in conversation:
            message = self.make_request_message(request)
            bot_handler.reset_transcript()
            bot.handle_message(message, bot_handler)
            response = bot_handler.unique_response()
            self.assertEqual(expected_response, response['content'])

    def validate_invalid_config(self, config_data: Dict[str, str], error_regexp: str) -> None:
        bot_class = type(get_bot_message_handler(self.bot_name))
        with self.assertRaisesRegexp(ConfigValidationError, error_regexp):
            bot_class.validate_config(config_data)

    def validate_valid_config(self, config_data: Dict[str, str]) -> None:
        bot_class = type(get_bot_message_handler(self.bot_name))
        bot_class.validate_config(config_data)

    def mock_http_conversation(self, test_name: str) -> Any:
        assert test_name is not None
        http_data = read_bot_fixture_data(self.bot_name, test_name)
        return mock_http_conversation(http_data)

    def mock_request_exception(self) -> Any:
        return mock_request_exception()

    def mock_config_info(self, config_info: Dict[str, str]) -> Any:
        return unittest.mock.patch('zulip_bots.test_lib.StubBotHandler.get_config_info', return_value=config_info)

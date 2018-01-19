from unittest.mock import patch
from unittest import TestCase

from typing import List, Dict, Any, Tuple

from zulip_bots.request_test_lib import (
    mock_http_conversation,
)

from zulip_bots.simple_lib import (
    SimpleStorage,
    SimpleMessageServer,
)

from zulip_bots.test_file_utils import (
    get_bot_message_handler,
    read_bot_fixture_data,
)

class StubBotHandler:
    def __init__(self):
        # type: () -> None
        self.storage = SimpleStorage()
        self.full_name = 'test-bot'
        self.email = 'test-bot@example.com'
        self.message_server = SimpleMessageServer()
        self.reset_transcript()

    def reset_transcript(self):
        # type: () -> None
        self.transcript = []  # type: List[Tuple[str, Dict[str, Any]]]

    def send_message(self, message):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        self.transcript.append(('send_message', message))
        return self.message_server.send(message)

    def send_reply(self, message, response):
        # type: (Dict[str, Any], str) -> Dict[str, Any]
        response_message = dict(
            content=response
        )
        self.transcript.append(('send_reply', response_message))
        return self.message_server.send(response_message)

    def update_message(self, message):
        # type: (Dict[str, Any]) -> None
        self.message_server.update(message)

    class BotQuitException(Exception):
        pass

    def quit(self, message = ""):
        # type: (str) -> None
        raise self.BotQuitException()

    def get_config_info(self, bot_name, optional=False):
        # type: (str, bool) -> Dict[str, Any]
        return {}

    def unique_reply(self):
        # type: () -> Dict[str, Any]
        responses = [
            message
            for (method, message)
            in self.transcript
            if method == 'send_reply'
        ]
        self.ensure_unique_response(responses)
        return responses[0]

    def unique_response(self):
        # type: () -> Dict[str, Any]
        responses = [
            message
            for (method, message)
            in self.transcript
        ]
        self.ensure_unique_response(responses)
        return responses[0]

    def ensure_unique_response(self, responses):
        # type: (List[Dict[str, Any]]) -> None
        if not responses:
            raise Exception('The bot is not responding for some reason.')
        if len(responses) > 1:
            raise Exception('The bot is giving too many responses for some reason.')

class BotTestCase(TestCase):
    bot_name = ''

    def _get_handlers(self):
        # type: () -> Tuple[Any, StubBotHandler]
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        if hasattr(bot, 'initialize'):
            bot.initialize(bot_handler)

        return (bot, bot_handler)

    def get_response(self, message):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        bot, bot_handler = self._get_handlers()
        bot_handler.reset_transcript()
        bot.handle_message(message, bot_handler)
        return bot_handler.unique_response()

    def make_request_message(self, content):
        # type: (str) -> Dict[str, Any]
        '''
        This is mostly used internally but
        tests can override this behavior by
        mocking/subclassing.
        '''
        message = dict(
            display_recipient='foo_stream',
            sender_email='foo@example.com',
            sender_full_name='Foo Test User',
            sender_id='123',
            content=content,
        )
        return message

    def get_reply_dict(self, request):
        # type: (str) -> Dict[str, Any]
        bot, bot_handler = self._get_handlers()
        message = self.make_request_message(request)
        bot_handler.reset_transcript()
        bot.handle_message(message, bot_handler)
        reply = bot_handler.unique_reply()
        return reply

    def verify_reply(self, request, response):
        # type: (str, str) -> None
        reply = self.get_reply_dict(request)
        self.assertEqual(response, reply['content'])

    def verify_dialog(self, conversation):
        # type: (List[Tuple[str, str]]) -> None

        # Start a new message handler for the full conversation.
        bot, bot_handler = self._get_handlers()

        for (request, expected_response) in conversation:
            message = self.make_request_message(request)
            bot_handler.reset_transcript()
            bot.handle_message(message, bot_handler)
            response = bot_handler.unique_response()
            self.assertEqual(expected_response, response['content'])

    def test_bot_usage(self):
        # type: () -> None
        bot = get_bot_message_handler(self.bot_name)
        self.assertNotEqual(bot.usage(), '')

    def test_bot_responds_to_empty_message(self) -> None:
        message = self.make_request_message('')

        # get_response will fail if we don't respond at all
        response = self.get_response(message)

        # we also want a non-blank response
        self.assertTrue(len(response['content']) >= 1)

    def mock_http_conversation(self, test_name):
        # type: (str) -> Any
        assert test_name is not None
        http_data = read_bot_fixture_data(self.bot_name, test_name)
        return mock_http_conversation(http_data)

    def mock_config_info(self, config_info):
        # type: (Dict[str, str]) -> Any
        return patch('zulip_bots.test_lib.StubBotHandler.get_config_info', return_value=config_info)

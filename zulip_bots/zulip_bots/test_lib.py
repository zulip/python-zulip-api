#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import os

import json
import logging
import mock
import requests
import unittest

from mock import MagicMock, patch, call

from zulip_bots.lib import StateHandler
import zulip_bots.lib
from six.moves import zip

from contextlib import contextmanager
from importlib import import_module
from unittest import TestCase

from typing import List, Dict, Any, Optional, Callable, Tuple
from types import ModuleType

from copy import deepcopy

from zulip_bots.simple_lib import (
    SimpleStorage,
    SimpleMessageServer,
)

class StubBotHandler:
    def __init__(self):
        # type: () -> None
        self.storage = SimpleStorage()
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

    def get_config_info(self, bot_name, optional=False):
        # type: (str, bool) -> Dict[str, Any]
        return None

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

class StubBotTestCase(TestCase):
    '''
    The goal for this class is to eventually replace
    BotTestCase for places where we may want more
    fine-grained control and less heavy setup.
    '''

    bot_name = ''

    def get_response(self, message):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        if hasattr(bot, 'initialize'):
            bot.initialize(bot_handler)

        bot_handler.reset_transcript()
        bot.handle_message(message, bot_handler)
        return bot_handler.unique_response()

    def verify_reply(self, request, response):
        # type: (str, str) -> None

        # Start a new message handler for the full conversation.
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        if hasattr(bot, 'initialize'):
            bot.initialize(bot_handler)

        message = dict(
            sender_email='foo@example.com',
            content=request,
        )
        bot_handler.reset_transcript()
        bot.handle_message(message, bot_handler)
        reply = bot_handler.unique_reply()
        self.assertEqual(response, reply['content'])

    def verify_dialog(self, conversation):
        # type: (List[Tuple[str, str]]) -> None

        # Start a new message handler for the full conversation.
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        for (request, expected_response) in conversation:
            message = dict(
                sender_email='foo@example.com',
                sender_full_name='Foo Test User',
                content=request,
            )
            bot_handler.reset_transcript()
            bot.handle_message(message, bot_handler)
            response = bot_handler.unique_response()
            self.assertEqual(expected_response, response['content'])

    def test_bot_usage(self):
        # type: () -> None
        bot = get_bot_message_handler(self.bot_name)
        self.assertNotEqual(bot.usage(), '')

    def mock_http_conversation(self, test_name):
        # type: (str) -> Any
        assert test_name is not None
        http_data = read_bot_fixture_data(self.bot_name, test_name)
        return mock_http_conversation(http_data)

    def mock_config_info(self, config_info):
        # type: (Dict[str, str]) -> Any
        return patch('zulip_bots.test_lib.StubBotHandler.get_config_info', return_value=config_info)

def get_bot_message_handler(bot_name):
    # type: (str) -> Any
    # message_handler is of type 'Any', since it can contain any bot's
    # handler class. Eventually, we want bot's handler classes to
    # inherit from a common prototype specifying the handle_message
    # function.
    lib_module = import_module('zulip_bots.bots.{bot}.{bot}'.format(bot=bot_name))  # type: Any
    return lib_module.handler_class()

def read_bot_fixture_data(bot_name, test_name):
    # type: (str, str) -> Dict[str, Any]
    base_path = os.path.realpath(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'bots', bot_name, 'fixtures'))
    http_data_path = os.path.join(base_path, '{}.json'.format(test_name))
    with open(http_data_path) as f:
        content = f.read()
    http_data = json.loads(content)
    return http_data

@contextmanager
def mock_http_conversation(http_data):
    # type: (Dict[str, Any]) -> Any
    """
    Use this context manager to mock and verify a bot's HTTP
    requests to the third-party API (and provide the correct
    third-party API response. This allows us to test things
    that would require the Internet without it).

    http_data should be fixtures data formatted like the data
    in zulip_bots/zulip_bots/bots/giphy/fixtures/test_normal.json
    """
    def get_response(http_response, http_headers):
        # type: (Dict[str, Any], Dict[str, Any]) -> Any
        """Creates a fake `requests` Response with a desired HTTP response and
        response headers.
        """
        mock_result = requests.Response()
        mock_result._content = json.dumps(http_response).encode()  # type: ignore # This modifies a "hidden" attribute.
        mock_result.status_code = http_headers.get('status', 200)
        return mock_result

    def assert_called_with_fields(mock_result, http_request, fields):
        # type: (Any, Dict[str, Any], List[str]) -> None
        """Calls `assert_called_with` on a mock object using an HTTP request.
        Uses `fields` to determine which keys to look for in HTTP request and
        to test; if a key is in `fields`, e.g., 'headers', it will be used in
        the assertion.
        """
        args = {}

        for field in fields:
            if field in http_request:
                args[field] = http_request[field]

        mock_result.assert_called_with(http_request['api_url'], **args)

    http_request = http_data.get('request')
    http_response = http_data.get('response')
    http_headers = http_data.get('response-headers')
    http_method = http_request.get('method', 'GET')

    if http_method == 'GET':
        with patch('requests.get') as mock_get:
            mock_get.return_value = get_response(http_response, http_headers)
            yield
            assert_called_with_fields(
                mock_get,
                http_request,
                ['params', 'headers']
            )
    else:
        with patch('requests.post') as mock_post:
            mock_post.return_value = get_response(http_response, http_headers)
            yield
            assert_called_with_fields(
                mock_post,
                http_request,
                ['params', 'headers', 'json']
            )

class BotTestCase(StubBotTestCase):
    """Test class for common Bot test helper methods"""
    bot_name = ''  # type: str

    def setUp(self):
        # type: () -> None
        # Mocking ExternalBotHandler
        self.patcher = patch('zulip_bots.lib.ExternalBotHandler', autospec=True)
        self.MockClass = self.patcher.start()
        self.mock_bot_handler = self.MockClass(None, None, None, None)
        self.mock_client = MagicMock()
        self.mock_client.get_storage.return_value = {'result': 'success', 'storage': {}}
        self.mock_client.update_storage.return_value = {'result': 'success'}
        self.mock_bot_handler.storage = StateHandler(self.mock_client)
        self.message_handler = get_bot_message_handler(self.bot_name)

    def tearDown(self):
        # type: () -> None
        self.patcher.stop()

    def initialize_bot(self):
        # type: () -> None
        self.message_handler.initialize(self.mock_bot_handler)

    def check_expected_responses(self, expectations, expected_method='send_reply',
                                 email="foo_sender@zulip.com", recipient="foo", subject="foo",
                                 sender_id=0, sender_full_name="Foo Bar", type="all"):
        # type: (List[Tuple[str, Any]], str, str, str, str, int, str, str) -> None
        # To test send_message, Any would be a Dict type,
        # to test send_reply, Any would be a str type.
        if type not in ["private", "stream", "all"]:
            logging.exception("check_expected_response expects type to be 'private', 'stream' or 'all'")

        private_message_template = {'type': "private", 'display_recipient': recipient,
                                    'sender_email': email, 'sender_id': sender_id,
                                    'sender_full_name': sender_full_name}
        stream_message_template = {'type': "stream", 'display_recipient': recipient,
                                   'subject': subject, 'sender_email': email, 'sender_id': sender_id,
                                   'sender_full_name': sender_full_name}

        message_templates = []
        if type in ["private", "all"]:
            message_templates.append(private_message_template)
        if type in ["stream", "all"]:
            message_templates.append(stream_message_template)

        initial_storage = deepcopy(self.mock_bot_handler.storage)
        for message_template in message_templates:
            # A new copy of the StateHandler is used for every new conversation with a
            # different base template. This avoids type="all" failing if the created state
            # of a prior conversation influences the current one.
            self.mock_bot_handler.storage = deepcopy(initial_storage)
            for m, r in expectations:
                # For calls with send_reply, r is a string (the content of a message),
                # so we need to add it to a Dict as the value of 'content'.
                # For calls with send_message, r is already a Dict.
                message = dict(message_template, content = m)
                response = {'content': r} if expected_method == 'send_reply' else r
                self.assert_bot_responses(message, (response, expected_method))

    def call_request(self, message, *responses):
        # type: (Dict[str, Any], *Tuple[Dict[str, Any], str]) -> None

        # Mock BotHandler; get instance
        instance = self.MockClass.return_value

        # Send message to the bot
        try:
            self.message_handler.handle_message(message, self.mock_bot_handler)
        except KeyError as key_err:
            raise Exception("Message tested likely required key {}.".format(key_err))

        # Determine which messaging functions are expected
        send_messages = [call(r[0]) for r in responses if r[1] == 'send_message']
        send_replies = [call(message, r[0]['content']) for r in responses if r[1] == 'send_reply']

        # Test that call were matching in quantity, and then in details
        fail_template = "\nMESSAGE:\n{}\nACTUAL CALLS:\n{}\nEXPECTED:\n{}\n"
        functions_to_test = (('send_message', instance.send_message, send_messages),
                             ('send_reply', instance.send_reply, send_replies))
        for version, actual, expected in functions_to_test:
            assert len(expected) == actual.call_count, (
                "Numbers of '{}' called do not match those expected ({} calls, {} expected)" +
                fail_template).format(version, actual.call_count, len(expected),
                                      message, actual.call_args_list, expected)
            if len(expected) > 0:
                try:
                    actual.assert_has_calls(expected)
                except AssertionError:
                    raise AssertionError(
                        ("Calls to '{}' do not match those expected" +
                         fail_template).format(version,
                                               message, actual.call_args_list, expected))
                actual.reset_mock()  # Ensure the call details are reset

    @contextmanager
    def mock_config_info(self, config_info):
        # type: (Dict[str, str]) -> Any
        self.mock_bot_handler.get_config_info.return_value = config_info
        yield
        self.mock_bot_handler.get_config_info.return_value = None

    def assert_bot_response(self, message, response, expected_method):
        # type: (Dict[str, Any], Dict[str, Any], str) -> None
        # Strictly speaking, this function is not needed anymore,
        # kept for now for legacy reasons.
        self.call_request(message, (response, expected_method))

    def assert_bot_responses(self, message, *response_list):
        # type: (Dict[str, Any], *Tuple[Dict[str, Any], str]) -> None
        self.call_request(message, *response_list)

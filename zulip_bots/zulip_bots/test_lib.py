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

def get_bot_message_handler(bot_name):
    # type: (str) -> Any
    # message_handler is of type 'Any', since it can contain any bot's
    # handler class. Eventually, we want bot's handler classes to
    # inherit from a common prototype specifying the handle_message
    # function.
    lib_module = import_module('zulip_bots.bots.{bot}.{bot}'.format(bot=bot_name))  # type: Any
    return lib_module.handler_class()

class BotTestCaseBase(TestCase):
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
        self.mock_bot_handler.send_message.return_value = {'id': 42}
        self.mock_bot_handler.send_reply.return_value = {'id': 42}
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

    @contextmanager
    def mock_http_conversation(self, test_name):
        # type: (str) -> Any
        """
        Use this context manager to mock and verify a bot's HTTP
        requests to the third-party API (and provide the correct
        third-party API response. This allows us to test things
        that would require the Internet without it).
        """
        assert test_name is not None
        base_path = os.path.realpath(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'bots', self.bot_name, 'fixtures'))
        http_data_path = os.path.join(base_path, '{}.json'.format(test_name))
        with open(http_data_path, 'r') as http_data_file:
            http_data = json.load(http_data_file)
            http_request = http_data.get('request')
            http_response = http_data.get('response')
            http_headers = http_data.get('response-headers')
            with patch('requests.get') as mock_get:
                mock_result = requests.Response()
                mock_result._content = json.dumps(http_response).encode()  # type: ignore # We are modifying a "hidden" attribute.
                mock_result.status_code = http_headers.get('status', 200)
                mock_get.return_value = mock_result
                yield
                if 'params' in http_request:
                    params = http_request.get('params', None)
                    mock_get.assert_called_with(http_request['api_url'], params=params)
                elif 'headers' in http_request:
                    headers = http_request.get('headers', None)
                    mock_get.assert_called_with(http_request['api_url'], headers=headers)
                else:
                    mock_get.assert_called_with(http_request['api_url'])

    def assert_bot_response(self, message, response, expected_method):
        # type: (Dict[str, Any], Dict[str, Any], str) -> None
        # Strictly speaking, this function is not needed anymore,
        # kept for now for legacy reasons.
        self.call_request(message, (response, expected_method))

    def assert_bot_responses(self, message, *response_list):
        # type: (Dict[str, Any], *Tuple[Dict[str, Any], str]) -> None
        self.call_request(message, *response_list)

class BotTestCase(BotTestCaseBase):
    """Test class extending BotTestCaseBase to add common default tests
    that should be run (by default) for all our bots"""
    def test_bot_usage(self):
        # type: () -> None
        self.assertNotEqual(self.message_handler.usage(), '')

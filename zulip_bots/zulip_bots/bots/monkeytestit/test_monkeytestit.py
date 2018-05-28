import unittest
from unittest import mock

from importlib import import_module
from zulip_bots.test_lib import BotTestCase


# TODO: Figure out a way to test bots that depends
# on the Python version of the environment.
@unittest.skip("Fails on Python3.4.")
class TestMonkeyTestitBot(BotTestCase):
    bot_name = "monkeytestit"

    def setUp(self):
        self.monkeytestit_class = import_module(
            "zulip_bots.bots.monkeytestit.monkeytestit").MonkeyTestitBot

    def test_bot_responds_to_empty_message(self):
        message = dict(
            content='',
            type='stream',
        )
        with mock.patch.object(self.monkeytestit_class, 'initialize', return_value=None):
            with self.mock_config_info({'api_key': "magic"}):
                res = self.get_response(message)
                self.assertTrue("Unknown command" in res['content'])

    def test_website_fail(self):
        message = dict(
            content='check https://website.com',
            type='stream',
        )
        with mock.patch.object(self.monkeytestit_class, 'initialize', return_value=None):
            with self.mock_config_info({'api_key': "magic"}):
                with self.mock_http_conversation('website_result_fail'):
                    res = self.get_response(message)
                    self.assertTrue("Status: tests_failed" in res['content'])

    def test_website_success(self):
        message = dict(
            content='check https://website.com',
            type='stream',
        )
        with mock.patch.object(self.monkeytestit_class, 'initialize', return_value=None):
            with self.mock_config_info({'api_key': "magic"}):
                with self.mock_http_conversation('website_result_success'):
                    res = self.get_response(message)
                    self.assertTrue("success" in res['content'])

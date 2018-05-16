#!/usr/bin/env python3
import os
import sys
import zulip_bots.run
from zulip_bots.lib import extract_query_without_mention
import unittest
from typing import Optional
from unittest import TestCase

from unittest import mock
from unittest.mock import patch


class TestDefaultArguments(TestCase):

    our_dir = os.path.dirname(__file__)
    path_to_bot = os.path.abspath(os.path.join(our_dir, 'bots/giphy/giphy.py'))

    @patch('sys.argv', ['zulip-run-bot', 'giphy', '--config-file', '/foo/bar/baz.conf'])
    @patch('zulip_bots.run.run_message_handler_for_bot')
    def test_argument_parsing_with_bot_name(self, mock_run_message_handler_for_bot: mock.Mock) -> None:
        with patch('zulip_bots.run.exit_gracefully_if_zulip_config_file_does_not_exist'):
            zulip_bots.run.main()

        mock_run_message_handler_for_bot.assert_called_with(bot_name='giphy',
                                                            config_file='/foo/bar/baz.conf',
                                                            bot_config_file=None,
                                                            lib_module=mock.ANY,
                                                            quiet=False)

    @patch('sys.argv', ['zulip-run-bot', path_to_bot, '--config-file', '/foo/bar/baz.conf'])
    @patch('zulip_bots.run.run_message_handler_for_bot')
    def test_argument_parsing_with_bot_path(self, mock_run_message_handler_for_bot: mock.Mock) -> None:
        with patch('zulip_bots.run.exit_gracefully_if_zulip_config_file_does_not_exist'):
            zulip_bots.run.main()

        mock_run_message_handler_for_bot.assert_called_with(
            bot_name='giphy',
            config_file='/foo/bar/baz.conf',
            bot_config_file=None,
            lib_module=mock.ANY,
            quiet=False)

    def test_adding_bot_parent_dir_to_sys_path_when_bot_name_specified(self) -> None:
        bot_name = 'any_bot_name'
        expected_bot_dir_path = os.path.join(
            os.path.dirname(zulip_bots.run.__file__),
            'bots',
            bot_name
        )
        self._test_adding_bot_parent_dir_to_sys_path(bot_qualifier=bot_name, bot_dir_path=expected_bot_dir_path)

    @patch('os.path.isfile', return_value=True)
    def test_adding_bot_parent_dir_to_sys_path_when_bot_path_specified(self, mock_os_path_isfile: mock.Mock) -> None:
        bot_path = '/path/to/bot'
        expected_bot_dir_path = '/path/to'
        self._test_adding_bot_parent_dir_to_sys_path(bot_qualifier=bot_path, bot_dir_path=expected_bot_dir_path)

    def _test_adding_bot_parent_dir_to_sys_path(self, bot_qualifier, bot_dir_path):
        # type: (str, str) -> None
        with patch('sys.argv', ['zulip-run-bot', bot_qualifier, '--config-file', '/path/to/config']):
            with patch('zulip_bots.run.import_module_from_source', return_value=mock.Mock()):
                with patch('zulip_bots.run.run_message_handler_for_bot'):
                    with patch('zulip_bots.run.exit_gracefully_if_zulip_config_file_does_not_exist'):
                        zulip_bots.run.main()

        self.assertIn(bot_dir_path, sys.path)


class TestBotLib(TestCase):
    def test_extract_query_without_mention(self) -> None:

        def test_message(name: str, message: str, expected_return: Optional[str]) -> None:
            mock_client = mock.MagicMock()
            mock_client.full_name = name
            mock_message = {'content': message}
            self.assertEqual(expected_return, extract_query_without_mention(mock_message, mock_client))
        test_message("xkcd", "@**xkcd**foo", "foo")
        test_message("xkcd", "@**xkcd** foo", "foo")
        test_message("xkcd", "@**xkcd** foo bar baz", "foo bar baz")
        test_message("xkcd", "@**xkcd**         foo bar baz", "foo bar baz")
        test_message("xkcd", "@**xkcd** 123_) (/&%) +}}}l", "123_) (/&%) +}}}l")
        test_message("brokenmention", "@**brokenmention* foo", None)
        test_message("nomention", "foo", None)
        test_message("Max Mustermann", "@**Max Mustermann** foo", "foo")
        test_message("Max (Mustermann)#(*$&12]\]", "@**Max (Mustermann)#(*$&12]\]** foo", "foo")

if __name__ == '__main__':
    unittest.main()

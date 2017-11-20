#!/usr/bin/env python
from __future__ import absolute_import

import importlib
import os
import zulip_bots.run
from zulip_bots.lib import extract_query_without_mention
import six
import unittest
import zulip

from importlib import import_module
from typing import Optional
from unittest import TestCase

if six.PY2:
    import mock
    from mock import patch
else:
    from unittest import mock
    from unittest.mock import patch

class TestDefaultArguments(TestCase):

    our_dir = os.path.dirname(__file__)
    path_to_bot = os.path.abspath(os.path.join(our_dir, 'bots/giphy/giphy.py'))

    @patch('sys.argv', ['zulip-run-bot', 'giphy', '--config-file', '/foo/bar/baz.conf'])
    @patch('zulip_bots.run.run_message_handler_for_bot')
    def test_argument_parsing_with_bot_name(self, mock_run_message_handler_for_bot):
        # type: (mock.Mock) -> None
        with patch('zulip_bots.run.exit_gracefully_if_config_file_does_not_exist'):
            zulip_bots.run.main()

        mock_run_message_handler_for_bot.assert_called_with(bot_name='giphy',
                                                            config_file='/foo/bar/baz.conf',
                                                            lib_module=mock.ANY,
                                                            quiet=False)

    @patch('sys.argv', ['zulip-run-bot', path_to_bot, '--config-file', '/foo/bar/baz.conf'])
    @patch('zulip_bots.run.run_message_handler_for_bot')
    def test_argument_parsing_with_bot_path(self, mock_run_message_handler_for_bot):
        # type: (mock.Mock) -> None
        with patch('zulip_bots.run.exit_gracefully_if_config_file_does_not_exist'):
            zulip_bots.run.main()

        mock_run_message_handler_for_bot.assert_called_with(
            bot_name='giphy',
            config_file='/foo/bar/baz.conf',
            lib_module=mock.ANY,
            quiet=False)

class TestBotLib(TestCase):
    def test_extract_query_without_mention(self):
        # type: () -> None

        def test_message(name, message, expected_return):
            # type: (str, str, Optional[str]) -> None
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

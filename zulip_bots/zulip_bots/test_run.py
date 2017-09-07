#!/usr/bin/env python
from __future__ import absolute_import

import importlib
import os
import zulip_bots.run
import six
import unittest
import zulip

from importlib import import_module
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
        zulip_bots.run.main()
        mock_run_message_handler_for_bot.assert_called_with(bot_name='giphy',
                                                            config_file='/foo/bar/baz.conf',
                                                            lib_module=mock.ANY,
                                                            quiet=False)

    @patch('sys.argv', ['zulip-run-bot', path_to_bot, '--config-file', '/foo/bar/baz.conf'])
    @patch('zulip_bots.run.run_message_handler_for_bot')
    def test_argument_parsing_with_bot_path(self, mock_run_message_handler_for_bot):
        zulip_bots.run.main()
        mock_run_message_handler_for_bot.assert_called_with(
            bot_name='giphy',
            config_file='/foo/bar/baz.conf',
            lib_module=mock.ANY,
            quiet=False)

if __name__ == '__main__':
    unittest.main()

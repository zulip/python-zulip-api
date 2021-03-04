#!/usr/bin/env python3

import argparse
import os
import io
import unittest
import zulip

from unittest import TestCase
from zulip import ZulipError
from unittest.mock import patch

class TestDefaultArguments(TestCase):

    def test_invalid_arguments(self) -> None:
        parser = zulip.add_default_arguments(argparse.ArgumentParser(usage="lorem ipsum"))
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new=io.StringIO()) as mock_stderr:
                parser.parse_args(['invalid argument'])
        self.assertEqual(cm.exception.code, 2)
        # Assert that invalid arguments exit with printing the full usage (non-standard behavior)
        self.assertTrue(mock_stderr.getvalue().startswith("""usage: lorem ipsum

optional arguments:
  -h, --help            show this help message and exit

Zulip API configuration:
  --site ZULIP_SITE     Zulip server URI
"""))

    @patch('os.path.exists', return_value=False)
    def test_config_path_with_tilde(self, mock_os_path_exists: bool) -> None:
        parser = zulip.add_default_arguments(argparse.ArgumentParser(usage="lorem ipsum"))
        test_path = '~/zuliprc'
        args = parser.parse_args(['--config-file', test_path])
        with self.assertRaises(ZulipError) as cm:
            zulip.init_from_options(args)
        expanded_test_path = os.path.abspath(os.path.expanduser(test_path))
        self.assertEqual(str(cm.exception), 'api_key or email not specified and '
                         'file {} does not exist'.format(expanded_test_path))

if __name__ == '__main__':
    unittest.main()

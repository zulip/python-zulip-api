import argparse
import io
import os
from unittest import TestCase
from unittest.mock import patch

import zulip
from zulip import ZulipError


class TestDefaultArguments(TestCase):
    def test_invalid_arguments(self) -> None:
        parser = zulip.add_default_arguments(argparse.ArgumentParser(usage="lorem ipsum"))
        with self.assertRaises(SystemExit) as cm:
            with patch("sys.stderr", new=io.StringIO()) as mock_stderr:
                parser.parse_args(["invalid argument"])
        self.assertEqual(cm.exception.code, 2)
        # Assert that invalid arguments exit with printing the full usage (non-standard behavior)
        self.assertRegex(
            mock_stderr.getvalue(),
            r"""^usage: lorem ipsum

(optional arguments|options):
  -h, --help            show this help message and exit

Zulip API configuration:
  --site ZULIP_SITE     Zulip server URI
""",
        )

    @patch("os.path.exists", return_value=False)
    def test_config_path_with_tilde(self, mock_os_path_exists: bool) -> None:
        parser = zulip.add_default_arguments(argparse.ArgumentParser(usage="lorem ipsum"))
        test_path = "~/zuliprc"
        args = parser.parse_args(["--config-file", test_path])
        with self.assertRaises(ZulipError) as cm:
            zulip.init_from_options(args)
        expanded_test_path = os.path.abspath(os.path.expanduser(test_path))
        self.assertEqual(
            str(cm.exception),
            f"api_key or email not specified and file {expanded_test_path} does not exist",
        )

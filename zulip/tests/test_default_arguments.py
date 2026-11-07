import argparse
import io
import os
import tempfile
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

    def _setup_test_dirs(self) -> tuple[str, str]:
        orig_cwd = os.getcwd()
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.addCleanup(os.chdir, orig_cwd)

        home_dir = os.path.join(temp_dir.name, "home")
        cwd_dir = os.path.join(temp_dir.name, "cwd")
        os.makedirs(home_dir)
        os.makedirs(cwd_dir)
        os.chdir(cwd_dir)

        patcher = patch.dict(os.environ, {"HOME": home_dir})
        patcher.start()
        self.addCleanup(patcher.stop)

        return home_dir, cwd_dir

    def test_default_config_fallback_to_home(self) -> None:
        home_dir, _ = self._setup_test_dirs()
        home_zuliprc = os.path.join(home_dir, ".zuliprc")
        with open(home_zuliprc, "w") as f:
            f.write("[api]\nemail=home@example.com\n")

        self.assertEqual(zulip.get_default_config_filename(), home_zuliprc)

    def test_default_config_cwd_dotfile_beats_home(self) -> None:
        home_dir, cwd_dir = self._setup_test_dirs()
        home_zuliprc = os.path.join(home_dir, ".zuliprc")
        with open(home_zuliprc, "w") as f:
            f.write("[api]\nemail=home@example.com\n")

        with open(os.path.join(cwd_dir, ".zuliprc"), "w") as f:
            f.write("[api]\nemail=dot@example.com\n")

        self.assertEqual(zulip.get_default_config_filename(), os.path.abspath(".zuliprc"))

    def test_default_config_cwd_zuliprc_beats_dotfile(self) -> None:
        home_dir, cwd_dir = self._setup_test_dirs()
        home_zuliprc = os.path.join(home_dir, ".zuliprc")
        with open(home_zuliprc, "w") as f:
            f.write("[api]\nemail=home@example.com\n")

        with open(os.path.join(cwd_dir, ".zuliprc"), "w") as f:
            f.write("[api]\nemail=dot@example.com\n")
        with open(os.path.join(cwd_dir, "zuliprc"), "w") as f:
            f.write("[api]\nemail=plain@example.com\n")

        self.assertEqual(zulip.get_default_config_filename(), os.path.abspath("zuliprc"))

    def test_default_config_ignores_directory_named_zuliprc(self) -> None:
        home_dir, cwd_dir = self._setup_test_dirs()
        home_zuliprc = os.path.join(home_dir, ".zuliprc")
        with open(home_zuliprc, "w") as f:
            f.write("[api]\nemail=home@example.com\n")

        # Create a directory named zuliprc instead of a file
        os.makedirs(os.path.join(cwd_dir, "zuliprc"))

        # Must ignore the directory and fall back to HOME/.zuliprc
        self.assertEqual(zulip.get_default_config_filename(), home_zuliprc)

    def test_default_config_no_files_and_no_home_returns_none(self) -> None:
        _, _ = self._setup_test_dirs()
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(zulip.get_default_config_filename())

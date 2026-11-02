import os
import subprocess
import sys
import tempfile
from unittest import TestCase

from typing_extensions import override

script_dir = os.path.dirname(__file__)
script_path = os.path.join(script_dir, "rss-bot")
repo_root = os.path.abspath(os.path.join(script_dir, "..", ".."))


class RssBotFeedTests(TestCase):
    @override
    def setUp(self) -> None:
        self.env = {**os.environ, "PYTHONPATH": repo_root}

    def test_empty_lines_and_comments_in_feed_file(self) -> None:
        """Verify that empty lines, whitespace, and comments in the feeds file
        do not crash rss-bot with IsADirectoryError (Zulip issue #920).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            feed_file = os.path.join(tmpdir, "feeds")
            data_dir = os.path.join(tmpdir, "data")
            with open(feed_file, "w") as f:
                f.write("\n   \n# This is a comment\n\n   # Indented comment\n\n")

            cmd = [
                sys.executable,
                script_path,
                f"--feed-file={feed_file}",
                f"--data-dir={data_dir}",
                "--user=bot@example.com",
                "--api-key=test_key",
                "--site=https://chat.zulip.org",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False, env=self.env)
            self.assertEqual(proc.returncode, 0, f"Process failed with stderr:\n{proc.stderr}")
            self.assertNotIn("IsADirectoryError", proc.stderr)

    def test_valid_feed_with_blank_lines_and_comments(self) -> None:
        """Verify that valid feed URLs are processed while blank lines and comments are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feed_file = os.path.join(tmpdir, "feeds")
            data_dir = os.path.join(tmpdir, "data")
            with open(feed_file, "w") as f:
                f.write("# Feeds list\n\nhttp://localhost/rss.xml\n   \n# End of feeds\n")

            cmd = [
                sys.executable,
                script_path,
                f"--feed-file={feed_file}",
                f"--data-dir={data_dir}",
                "--user=bot@example.com",
                "--api-key=test_key",
                "--site=https://chat.zulip.org",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False, env=self.env)
            self.assertEqual(proc.returncode, 0, f"Process failed with stderr:\n{proc.stderr}")
            # Ensure the cache file for localhost was created
            expected_hash_file = os.path.join(data_dir, "localhost")
            self.assertTrue(
                os.path.exists(expected_hash_file),
                f"Expected cache file {expected_hash_file} was not created",
            )

    def test_missing_feed_file_exits_with_error(self) -> None:
        """Verify that attempting to read a non-existent feed file exits with error status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feed_file = os.path.join(tmpdir, "non_existent_feeds")
            data_dir = os.path.join(tmpdir, "data")

            cmd = [
                sys.executable,
                script_path,
                f"--feed-file={feed_file}",
                f"--data-dir={data_dir}",
                "--user=bot@example.com",
                "--api-key=test_key",
                "--site=https://chat.zulip.org",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False, env=self.env)
            self.assertEqual(proc.returncode, 1)

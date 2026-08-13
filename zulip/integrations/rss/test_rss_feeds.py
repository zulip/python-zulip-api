import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.dirname(__file__))

from rss_feeds import parse_feed_file_lines


class TestRssFeedParsing(TestCase):
    def test_skips_blank_lines(self) -> None:
        lines = ["https://example.com/feed", "", "  ", "https://other.test/rss"]
        self.assertEqual(
            parse_feed_file_lines(lines),
            ["https://example.com/feed", "https://other.test/rss"],
        )

    def test_strips_whitespace(self) -> None:
        self.assertEqual(parse_feed_file_lines(["  https://example.com/feed  \n"]), ["https://example.com/feed"])

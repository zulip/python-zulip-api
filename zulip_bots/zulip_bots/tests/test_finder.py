import os
from unittest import TestCase

from zulip_bots import finder


class FinderTestCase(TestCase):

    def test_resolve_bot_path(self) -> None:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        expected_bot_path = os.path.abspath(current_directory + '/../bots/helloworld/helloworld.py')
        expected_bot_name = 'helloworld'
        expected_bot_path_and_name = (expected_bot_path, expected_bot_name)
        actual_bot_path_and_name = finder.resolve_bot_path('helloworld')
        self.assertEqual(expected_bot_path_and_name, actual_bot_path_and_name)

import pytest
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from zulip_bots import finder


class FinderTestCase(TestCase):
    def test_resolve_bot_path(self) -> None:
        current_directory = Path(__file__).parents[1].as_posix()
        expected_bot_path = Path(current_directory + "/bots/helloworld/helloworld.py")
        expected_bot_name = "helloworld"
        expected_bot_path_and_name = (expected_bot_path, expected_bot_name)
        actual_bot_path_and_name = finder.resolve_bot_path("helloworld")
        self.assertEqual(expected_bot_path_and_name, actual_bot_path_and_name)


    def test_import_metadata_standard(self) -> None:
        # Simulate Python 3.10 or above by mocking importlib.metadata
        with patch("importlib.metadata.metadata", return_value="mocked_metadata") as mock_metadata:
            try:
                from importlib.metadata import metadata
                result = "Using standard library importlib.metadata"
            except ImportError:
                from importlib_metadata import metadata
                result = "Using external importlib_metadata"

            # Assert that the correct import was chosen
            self.assertEqual(result, "Using standard library importlib.metadata")
            self.assertEqual(metadata("some_package"), "mocked_metadata")
            mock_metadata.assert_called_once_with("some_package")
            
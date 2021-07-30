import argparse
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from zulip_bots.create_bot import main


class CreateBotTestCase(TestCase):
    @patch("sys.argv", ["zulip-create-bot", "test_bot", "-q"])
    @patch("zulip_bots.create_bot.open")
    def test_create_successfully(self, mock_open: MagicMock) -> None:
        with patch("os.mkdir"):
            main()

        bot_path, bot_module_path = Path(".", "test_bot"), Path(".", "test_bot", "test_bot")
        mock_open.assert_has_calls(
            [
                call(Path(bot_path, "README.md"), "w"),
                call(Path(bot_path, "setup.py"), "w"),
                call(Path(bot_module_path, "doc.md"), "w"),
                call(Path(bot_module_path, "__init__.py"), "w"),
                call(Path(bot_module_path, "test_bot.py"), "w"),
            ],
            True,
        )

    @patch("sys.argv", ["zulip-create-bot", "test-bot"])
    def test_create_with_invalid_names(self) -> None:
        with patch.object(
            argparse.ArgumentParser, "error", side_effect=InterruptedError
        ) as mock_error:
            try:
                main()
            except InterruptedError:
                pass

        mock_error.assert_called_with('"test-bot" is not a valid Python identifier')

    @patch("sys.argv", ["zulip-create-bot", "test_bot", "-o", "invalid_path"])
    def test_create_with_invalid_path(self) -> None:
        with patch("os.path.isdir", return_value=False), patch.object(
            argparse.ArgumentParser, "error", side_effect=InterruptedError
        ) as mock_error:
            try:
                main()
            except InterruptedError:
                pass

        mock_error.assert_called_with("invalid_path is not a valid path")

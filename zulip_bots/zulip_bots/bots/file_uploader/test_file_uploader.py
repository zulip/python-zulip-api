from unittest.mock import patch, MagicMock, Mock

from zulip_bots.test_lib import (
    get_bot_message_handler,
    StubBotHandler,
    BotTestCase,
    DefaultTests,
)

from pathlib import Path

class TestFileUploaderBot(BotTestCase, DefaultTests):
    bot_name = "file_uploader"

    @patch('pathlib.Path.is_file', return_value=False)
    def test_file_not_found(self, is_file: Mock) -> None:
        self.verify_reply('file.txt', 'File `file.txt` not found')

    @patch('pathlib.Path.resolve', return_value=Path('/file.txt'))
    @patch('pathlib.Path.is_file', return_value=True)
    def test_file_upload_failed(self, is_file: Mock, resolve: Mock) -> None:
        server_reply = dict(result='', msg='error')
        with patch('zulip_bots.test_lib.StubBotHandler.upload_file_from_path',
                   return_value=server_reply) as m:
            self.verify_reply('file.txt', 'Failed to upload `/file.txt` file: error')

    @patch('pathlib.Path.resolve', return_value=Path('/file.txt'))
    @patch('pathlib.Path.is_file', return_value=True)
    def test_file_upload_success(self, is_file: Mock, resolve: Mock) -> None:
        server_reply = dict(result='success', uri='https://file/uri')
        with patch('zulip_bots.test_lib.StubBotHandler.upload_file_from_path',
                   return_value=server_reply) as m:
            self.verify_reply('file.txt', '[file.txt](https://file/uri)')

    def test_help(self):
        self.verify_reply('help',
                          ('Use this bot with any of the following commands:'
                           '\n* `@uploader <local_file_path>` : Upload a file, where `<local_file_path>` is the path to the file'
                           '\n* `@uploader help` : Display help message'))

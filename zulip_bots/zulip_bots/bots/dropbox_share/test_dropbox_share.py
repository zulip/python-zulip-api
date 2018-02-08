from zulip_bots.test_lib import BotTestCase
from typing import List
from unittest.mock import patch

from zulip_bots.bots.dropbox_share.test_util import (
    MockFileMetadata,
    MockListFolderResult,
    MockSearchMatch,
    MockSearchResult,
    MockPathLinkMetadata,
    MockHttpResponse
)

def get_files_list(*args, **kwargs):
    return MockListFolderResult(
        entries = [
            MockFileMetadata('foo', '/foo'),
            MockFileMetadata('boo', '/boo')
        ],
        has_more = False
    )

def create_file(*args, **kwargs):
    return MockFileMetadata('foo', '/foo')

def download_file(*args, **kwargs):
    return [MockFileMetadata('foo', '/foo'), MockHttpResponse('boo')]

def search_files(*args, **kwargs):
    return MockSearchResult([
        MockSearchMatch(
            MockFileMetadata('foo', '/foo')
        ),
        MockSearchMatch(
            MockFileMetadata('fooboo', '/fooboo')
        )
    ])

def get_shared_link(*args, **kwargs):
    return MockPathLinkMetadata('http://www.foo.com/boo')

def get_help() -> str:
    return '''
    Example commands:

    ```
    @mention-bot usage: see usage examples
    @mention-bot mkdir: create a folder
    @mention-bot ls: list a folder
    @mention-bot write: write text
    @mention-bot rm: remove a file or folder
    @mention-bot read: read a file
    @mention-bot search: search a file/folder
    @mention-bot share: get a shareable link for the file/folder
    ```
    '''

class TestDropboxBot(BotTestCase):
    bot_name = "dropbox_share"
    config_info = {"access_token": "1234567890"}

    def test_bot_responds_to_empty_message(self):
        with self.mock_config_info(self.config_info):
            self.verify_reply('', get_help())
            self.verify_reply('help', get_help())

    def test_dbx_ls(self):
        bot_response = " - [foo](https://www.dropbox.com/home/foo)\n"\
                       " - [boo](https://www.dropbox.com/home/boo)"
        with patch('dropbox.dropbox.Dropbox.files_list_folder', side_effect=get_files_list), \
                self.mock_config_info(self.config_info):
            self.verify_reply("ls", bot_response)

    def test_dbx_mkdir(self):
        bot_response = "CREATED FOLDER: [foo](https://www.dropbox.com/home/foo)"
        with patch('dropbox.dropbox.Dropbox.files_create_folder', side_effect=create_file), \
                self.mock_config_info(self.config_info):
            self.verify_reply('mkdir foo', bot_response)

    def test_dbx_rm(self):
        bot_response = "DELETED File/Folder : [foo](https://www.dropbox.com/home/foo)"
        with patch('dropbox.dropbox.Dropbox.files_delete', side_effect=create_file), \
                self.mock_config_info(self.config_info):
            self.verify_reply('rm foo', bot_response)

    def test_dbx_write(self):
        bot_response = "Written to file: [foo](https://www.dropbox.com/home/foo)"
        with patch('dropbox.dropbox.Dropbox.files_upload', side_effect=create_file), \
                self.mock_config_info(self.config_info):
            self.verify_reply('write foo boo', bot_response)

    def test_dbx_read(self):
        bot_response = "**foo** :\nboo"
        with patch('dropbox.dropbox.Dropbox.files_download', side_effect=download_file), \
                self.mock_config_info(self.config_info):
            self.verify_reply('read foo', bot_response)

    def test_dbx_search(self):
        bot_response = " - [foo](https://www.dropbox.com/home/foo)\n"\
                       " - [fooboo](https://www.dropbox.com/home/fooboo)"
        with patch('dropbox.dropbox.Dropbox.files_search', side_effect=search_files), \
                self.mock_config_info(self.config_info):
            self.verify_reply('search foo', bot_response)

    def test_dbx_share(self):
        bot_response = 'http://www.foo.com/boo'
        with patch('dropbox.dropbox.Dropbox.sharing_create_shared_link', side_effect=get_shared_link), \
                self.mock_config_info(self.config_info):
            self.verify_reply('share boo', bot_response)

    def test_invalid_commands(self):
        ls_error_response = "ERROR: syntax: ls <optional_path>"
        mkdir_error_response = "ERROR: syntax: mkdir <path>"
        rm_error_response = "ERROR: syntax: rm <path>"
        write_error_response = "ERROR: syntax: write <path> <some_text>"
        search_error_response = "ERROR: syntax: search <path> <some_text> <max_results>"
        share_error_response = "ERROR: syntax: share <path>"

        with self.mock_config_info(self.config_info):
            # ls
            self.verify_reply("ls foo boo", ls_error_response)
            # mkdir
            self.verify_reply("mkdir foo boo", mkdir_error_response)
            # rm
            self.verify_reply("rm foo boo", rm_error_response)
            # write
            self.verify_reply("write foo", write_error_response)
            # share
            self.verify_reply("share foo boo", share_error_response)

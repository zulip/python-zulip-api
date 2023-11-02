from typing import Final
from unittest.mock import patch

from zulip_bots.bots.dropbox_share.test_util import (
    MockFileMetadata,
    MockHttpResponse,
    MockListFolderResult,
    MockPathLinkMetadata,
    MockSearchMatch,
    MockSearchResult,
)
from zulip_bots.test_lib import BotTestCase, DefaultTests


def get_root_files_list(*args, **kwargs):
    return MockListFolderResult(
        entries=[MockFileMetadata("foo", "/foo"), MockFileMetadata("boo", "/boo")], has_more=False
    )


def get_folder_files_list(*args, **kwargs):
    return MockListFolderResult(
        entries=[
            MockFileMetadata("moo", "/foo/moo"),
            MockFileMetadata("noo", "/foo/noo"),
        ],
        has_more=False,
    )


def get_empty_files_list(*args, **kwargs):
    return MockListFolderResult(entries=[], has_more=False)


def create_file(*args, **kwargs):
    return MockFileMetadata("foo", "/foo")


def download_file(*args, **kwargs):
    return [MockFileMetadata("foo", "/foo"), MockHttpResponse("boo")]


def search_files(*args, **kwargs):
    return MockSearchResult(
        [
            MockSearchMatch(MockFileMetadata("foo", "/foo")),
            MockSearchMatch(MockFileMetadata("fooboo", "/fooboo")),
        ]
    )


def get_empty_search_result(*args, **kwargs):
    return MockSearchResult([])


def get_shared_link(*args, **kwargs):
    return MockPathLinkMetadata("http://www.foo.com/boo")


def get_help() -> str:
    return """
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
    """


class TestDropboxBot(BotTestCase, DefaultTests):
    bot_name = "dropbox_share"
    config_info: Final = {"access_token": "1234567890"}

    def test_bot_responds_to_empty_message(self):
        with self.mock_config_info(self.config_info):
            self.verify_reply("", get_help())
            self.verify_reply("help", get_help())

    def test_dbx_ls_root(self):
        bot_response = (
            " - [foo](https://www.dropbox.com/home/foo)\n"
            " - [boo](https://www.dropbox.com/home/boo)"
        )
        with patch(
            "dropbox.Dropbox.files_list_folder", side_effect=get_root_files_list
        ), self.mock_config_info(self.config_info):
            self.verify_reply("ls", bot_response)

    def test_dbx_ls_folder(self):
        bot_response = (
            " - [moo](https://www.dropbox.com/home/foo/moo)\n"
            " - [noo](https://www.dropbox.com/home/foo/noo)"
        )
        with patch(
            "dropbox.Dropbox.files_list_folder", side_effect=get_folder_files_list
        ), self.mock_config_info(self.config_info):
            self.verify_reply("ls foo", bot_response)

    def test_dbx_ls_empty(self):
        bot_response = "`No files available`"
        with patch(
            "dropbox.Dropbox.files_list_folder", side_effect=get_empty_files_list
        ), self.mock_config_info(self.config_info):
            self.verify_reply("ls", bot_response)

    def test_dbx_ls_error(self):
        bot_response = (
            "Please provide a correct folder path\n"
            "Usage: `ls <foldername>` to list folders in directory\n"
            "or simply `ls` for listing folders in the root directory"
        )
        with patch(
            "dropbox.Dropbox.files_list_folder", side_effect=Exception()
        ), self.mock_config_info(self.config_info):
            self.verify_reply("ls", bot_response)

    def test_dbx_mkdir(self):
        bot_response = "CREATED FOLDER: [foo](https://www.dropbox.com/home/foo)"
        with patch(
            "dropbox.Dropbox.files_create_folder", side_effect=create_file
        ), self.mock_config_info(self.config_info):
            self.verify_reply("mkdir foo", bot_response)

    def test_dbx_mkdir_error(self):
        bot_response = (
            "Please provide a correct folder path and name.\n"
            "Usage: `mkdir <foldername>` to create a folder."
        )
        with patch(
            "dropbox.Dropbox.files_create_folder", side_effect=Exception()
        ), self.mock_config_info(self.config_info):
            self.verify_reply("mkdir foo/bar", bot_response)

    def test_dbx_rm(self):
        bot_response = "DELETED File/Folder : [foo](https://www.dropbox.com/home/foo)"
        with patch("dropbox.Dropbox.files_delete", side_effect=create_file), self.mock_config_info(
            self.config_info
        ):
            self.verify_reply("rm foo", bot_response)

    def test_dbx_rm_error(self):
        bot_response = (
            "Please provide a correct folder path and name.\n"
            "Usage: `rm <foldername>` to delete a folder in root directory."
        )
        with patch("dropbox.Dropbox.files_delete", side_effect=Exception()), self.mock_config_info(
            self.config_info
        ):
            self.verify_reply("rm foo", bot_response)

    def test_dbx_write(self):
        bot_response = "Written to file: [foo](https://www.dropbox.com/home/foo)"
        with patch("dropbox.Dropbox.files_upload", side_effect=create_file), self.mock_config_info(
            self.config_info
        ):
            self.verify_reply("write foo boo", bot_response)

    def test_dbx_write_error(self):
        bot_response = (
            "Incorrect file path or file already exists.\nUsage: `write <filename> CONTENT`"
        )
        with patch("dropbox.Dropbox.files_upload", side_effect=Exception()), self.mock_config_info(
            self.config_info
        ):
            self.verify_reply("write foo boo", bot_response)

    def test_dbx_read(self):
        bot_response = "**foo** :\nboo"
        with patch(
            "dropbox.Dropbox.files_download", side_effect=download_file
        ), self.mock_config_info(self.config_info):
            self.verify_reply("read foo", bot_response)

    def test_dbx_read_error(self):
        bot_response = (
            "Please provide a correct file path\n"
            "Usage: `read <filename>` to read content of a file"
        )
        with patch(
            "dropbox.Dropbox.files_download", side_effect=Exception()
        ), self.mock_config_info(self.config_info):
            self.verify_reply("read foo", bot_response)

    def test_dbx_search(self):
        bot_response = " - [foo](https://www.dropbox.com/home/foo)\n - [fooboo](https://www.dropbox.com/home/fooboo)"
        with patch("dropbox.Dropbox.files_search", side_effect=search_files), self.mock_config_info(
            self.config_info
        ):
            self.verify_reply("search foo", bot_response)

    def test_dbx_search_empty(self):
        bot_response = (
            "No files/folders found matching your query.\n"
            "For file name searching, the last token is used for prefix matching"
            " (i.e. “bat c” matches “bat cave” but not “batman car”)."
        )
        with patch(
            "dropbox.Dropbox.files_search", side_effect=get_empty_search_result
        ), self.mock_config_info(self.config_info):
            self.verify_reply("search boo --fd foo", bot_response)

    def test_dbx_search_error(self):
        bot_response = (
            "Usage: `search <foldername> query --mr 10 --fd <folderName>`\n"
            "Note:`--mr <int>` is optional and is used to specify maximun results.\n"
            "     `--fd <folderName>` to search in specific folder."
        )
        with patch("dropbox.Dropbox.files_search", side_effect=Exception()), self.mock_config_info(
            self.config_info
        ):
            self.verify_reply("search foo", bot_response)

    def test_dbx_share(self):
        bot_response = "http://www.foo.com/boo"
        with patch(
            "dropbox.Dropbox.sharing_create_shared_link", side_effect=get_shared_link
        ), self.mock_config_info(self.config_info):
            self.verify_reply("share boo", bot_response)

    def test_dbx_share_error(self):
        bot_response = "Please provide a correct file name.\nUsage: `share <filename>`"
        with patch(
            "dropbox.Dropbox.sharing_create_shared_link", side_effect=Exception()
        ), self.mock_config_info(self.config_info):
            self.verify_reply("share boo", bot_response)

    def test_dbx_help(self):
        bot_response = "syntax: ls <optional_path>"
        with self.mock_config_info(self.config_info):
            self.verify_reply("help ls", bot_response)

    def test_dbx_usage(self):
        bot_response = """
    Usage:
    ```
    @dropbox ls - Shows files/folders in the root folder.
    @dropbox mkdir foo - Make folder named foo.
    @dropbox ls foo/boo - Shows the files/folders in foo/boo folder.
    @dropbox write test hello world - Write "hello world" to the file 'test'.
    @dropbox rm test - Remove the file/folder test.
    @dropbox read foo - Read the contents of file/folder foo.
    @dropbox share foo - Get shareable link for the file/folder foo.
    @dropbox search boo - Search for boo in root folder and get at max 20 results.
    @dropbox search boo --mr 10 - Search for boo and get at max 10 results.
    @dropbox search boo --fd foo - Search for boo in folder foo.
    ```
    """
        with self.mock_config_info(self.config_info):
            self.verify_reply("usage", bot_response)

    def test_invalid_commands(self):
        ls_error_response = "ERROR: syntax: ls <optional_path>"
        mkdir_error_response = "ERROR: syntax: mkdir <path>"
        rm_error_response = "ERROR: syntax: rm <path>"
        write_error_response = "ERROR: syntax: write <path> <some_text>"
        share_error_response = "ERROR: syntax: share <path>"
        usage_error_response = "ERROR: syntax: usage"

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
            # usage
            self.verify_reply("usage foo", usage_error_response)

    def test_unkown_command(self):
        bot_response = """ERROR: unrecognized command

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
    """
        with self.mock_config_info(self.config_info):
            self.verify_reply("unknown command", bot_response)

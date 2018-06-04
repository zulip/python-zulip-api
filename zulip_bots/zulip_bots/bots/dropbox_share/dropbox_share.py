from dropbox.dropbox import Dropbox
from typing import Any, Dict, List, Tuple
import re

URL = "[{name}](https://www.dropbox.com/home{path})"

class DropboxHandler(object):
    '''
    This bot allows you to easily share, search and upload files
    between zulip and your dropbox account.
    '''

    def initialize(self, bot_handler: Any) -> None:
        self.config_info = bot_handler.get_config_info('dropbox_share')
        self.ACCESS_TOKEN = self.config_info.get('access_token')
        self.client = Dropbox(self.ACCESS_TOKEN)

    def usage(self) -> str:
        return get_help()

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        command = message['content']
        if command == "":
            command = "help"
        msg = dbx_command(self.client, command)
        bot_handler.send_reply(message, msg)

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

def get_usage_examples() -> str:
    return '''
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
    '''

REGEXES = dict(
    command='(ls|mkdir|read|rm|write|search|usage|help)',
    path='(\S+)',
    optional_path='(\S*)',
    some_text='(.+?)',
    folder='?(?:--fd (\S+))?',
    max_results='?(?:--mr (\d+))?'
)

def get_commands() -> Dict[str, Tuple[Any, List[str]]]:
    return {
        'help': (dbx_help, ['command']),
        'ls': (dbx_ls, ['optional_path']),
        'mkdir': (dbx_mkdir, ['path']),
        'rm': (dbx_rm, ['path']),
        'write': (dbx_write, ['path', 'some_text']),
        'read': (dbx_read, ['path']),
        'search': (dbx_search, ['some_text', 'folder', 'max_results']),
        'share': (dbx_share, ['path']),
        'usage': (dbx_usage, []),
    }

def dbx_command(client: Any, cmd: str) -> str:
    cmd = cmd.strip()
    if cmd == 'help':
        return get_help()
    cmd_name = cmd.split()[0]
    cmd_args = cmd[len(cmd_name):].strip()
    commands = get_commands()
    if cmd_name not in commands:
        return 'ERROR: unrecognized command\n' + get_help()
    f, arg_names = commands[cmd_name]
    partial_regexes = [REGEXES[a] for a in arg_names]
    regex = ' '.join(partial_regexes)
    regex += '$'
    m = re.match(regex, cmd_args)
    if m:
        return f(client, *m.groups())
    else:
        return 'ERROR: ' + syntax_help(cmd_name)

def syntax_help(cmd_name: str) -> str:
    commands = get_commands()
    f, arg_names = commands[cmd_name]
    arg_syntax = ' '.join('<' + a + '>' for a in arg_names)
    if arg_syntax:
        cmd = cmd_name + ' ' + arg_syntax
    else:
        cmd = cmd_name
    return 'syntax: {}'.format(cmd)

def dbx_help(client: Any, cmd_name: str) -> str:
    return syntax_help(cmd_name)

def dbx_usage(client: Any) -> str:
    return get_usage_examples()

def dbx_mkdir(client: Any, fn: str) -> str:
    fn = '/' + fn  # foo/boo -> /foo/boo
    try:
        result = client.files_create_folder(fn)
        msg = "CREATED FOLDER: " + URL.format(name=result.name, path=result.path_lower)
    except Exception:
        msg = "Please provide a correct folder path and name.\n"\
              "Usage: `mkdir <foldername>` to create a folder."

    return msg

def dbx_ls(client: Any, fn: str) -> str:
    if fn != '':
        fn = '/' + fn

    try:
        result = client.files_list_folder(fn)
        files_list = []  # type: List[str]
        for meta in result.entries:
            files_list += [" - " + URL.format(name=meta.name, path=meta.path_lower)]

        msg = '\n'.join(files_list)
        if msg is '':
            msg = '`No files available`'

    except Exception:
        msg = "Please provide a correct folder path\n"\
              "Usage: `ls <foldername>` to list folders in directory\n"\
              "or simply `ls` for listing folders in the root directory"

    return msg

def dbx_rm(client: Any, fn: str) -> str:
    fn = '/' + fn

    try:
        result = client.files_delete(fn)
        msg = "DELETED File/Folder : " + URL.format(name=result.name, path=result.path_lower)
    except Exception:
        msg = "Please provide a correct folder path and name.\n"\
              "Usage: `rm <foldername>` to delete a folder in root directory."
    return msg

def dbx_write(client: Any, fn: str, content: str) -> str:
    fn = '/' + fn

    try:
        result = client.files_upload(content.encode(), fn)
        msg = "Written to file: " + URL.format(name=result.name, path=result.path_lower)
    except Exception:
        msg = "Incorrect file path or file already exists.\n"\
              "Usage: `write <filename> CONTENT`"

    return msg

def dbx_read(client: Any, fn: str) -> str:
    fn = '/' + fn

    try:
        result = client.files_download(fn)
        msg = "**{}** :\n{}".format(result[0].name, result[1].text)
    except Exception:
        msg = "Please provide a correct file path\n"\
              "Usage: `read <filename>` to read content of a file"

    return msg

def dbx_search(client: Any, query: str, folder: str, max_results: str) -> str:
        if folder is None:
            folder = ''
        else:
            folder = '/' + folder
        if max_results is None:
            max_results = '20'
        try:
            result = client.files_search(folder, query, max_results=int(max_results))
            msg_list = []
            count = 0
            for entry in result.matches:
                file_info = entry.metadata
                count += 1
                msg_list += [" - " + URL.format(name=file_info.name, path=file_info.path_lower)]
            msg = '\n'.join(msg_list)

        except Exception:
            msg = "Usage: `search <foldername> query --mr 10 --fd <folderName>`\n"\
                  "Note:`--mr <int>` is optional and is used to specify maximun results.\n"\
                  "     `--fd <folderName>` to search in specific folder."

        if msg == '':
            msg = "No files/folders found matching your query.\n"\
                  "For file name searching, the last token is used for prefix matching"\
                  " (i.e. “bat c” matches “bat cave” but not “batman car”)."

        return msg

def dbx_share(client: Any, fn: str):
    fn = '/' + fn
    try:
        result = client.sharing_create_shared_link(fn)
        msg = result.url
    except Exception:
        msg = "Please provide a correct file name.\n"\
              "Usage: `share <filename>`"

    return msg

handler_class = DropboxHandler

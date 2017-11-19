#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from zulip_bots.test_lib import BotTestCase
from zulip_bots.lib import StateHandler
from zulip_bots.bots.virtual_fs.virtual_fs import get_help

class TestVirtualFsBot(BotTestCase):
    bot_name = "virtual_fs"
    help_txt = ('foo_sender@zulip.com:\n\nThis bot implements a virtual file system for a stream.\n'
                'The locations of text are persisted for the lifetime of the bot\n'
                'running, and if you rename a stream, you will lose the info.\n'
                'Example commands:\n\n```\n'
                '@mention-bot sample_conversation: sample conversation with the bot\n'
                '@mention-bot mkdir: create a directory\n'
                '@mention-bot ls: list a directory\n'
                '@mention-bot cd: change directory\n'
                '@mention-bot pwd: show current path\n'
                '@mention-bot write: write text\n'
                '@mention-bot read: read text\n'
                '@mention-bot rm: remove a file\n'
                '@mention-bot rmdir: remove a directory\n'
                '```\n'
                'Use commands like `@mention-bot help write` for more details on specific\ncommands.\n')

    sample_conversation_text = ('cd /\nCurrent path: /\n\n'
                                'cd /home\nERROR: invalid path\n\n'
                                'cd .\nERROR: invalid path\n\n'
                                'mkdir home\ndirectory created\n\n'
                                'cd home\nCurrent path: /home/\n\n'
                                'cd /home/\nCurrent path: /home/\n\n'
                                'mkdir stuff/\nERROR: stuff/ is not a valid name\n\n'
                                'mkdir stuff\ndirectory created\n\n'
                                'write stuff/file1 something\nfile written\n\n'
                                'read stuff/file1\nsomething\n\n'
                                'read /home/stuff/file1\nsomething\n\n'
                                'read home/stuff/file1\nERROR: file does not exist\n\n'
                                'pwd    \n/home/\n\n'
                                'pwd bla\nERROR: syntax: pwd\n\n'
                                'ls bla foo\nERROR: syntax: ls <optional_path>\n\n'
                                'cd /\nCurrent path: /\n\n'
                                'rm home\nERROR: /home/ is a directory, file required\n\n'
                                'rmdir home\nremoved\n\n'
                                'ls  \nWARNING: directory is empty\n\n'
                                'cd home\nERROR: invalid path\n\n'
                                'read /home/stuff/file1\nERROR: file does not exist\n\n'
                                'cd /\nCurrent path: /\n\n'
                                'write /foo contents of /foo\nfile written\n\n'
                                'read /foo\ncontents of /foo\n\n'
                                'write /bar Contents: bar bar\nfile written\n\n'
                                'read /bar\nContents: bar bar\n\n'
                                'write /bar invalid\nERROR: file already exists\n\n'
                                'rm /bar\nremoved\n\n'
                                'rm /bar\nERROR: file does not exist\n\n'
                                'write /bar new bar\nfile written\n\n'
                                'read /bar\nnew bar\n\n'
                                'write /yo/invalid whatever\nERROR: /yo is not a directory\n\n'
                                'mkdir /yo\ndirectory created\n\n'
                                'read /yo\nERROR: /yo/ is a directory, file required\n\n'
                                'ls /yo\nWARNING: directory is empty\n\n'
                                'read /yo/nada\nERROR: file does not exist\n\n'
                                'write /yo whatever\nERROR: file already exists\n\n'
                                'write /yo/apple red\nfile written\n\n'
                                'read /yo/apple\nred\n\n'
                                'mkdir /yo/apple\nERROR: file already exists\n\n'
                                'ls /invalid\nERROR: file does not exist\n\n'
                                'ls /foo\nERROR: /foo is not a directory\n\n'
                                'ls /\n* /*bar*\n* /*foo*\n* /yo/\n\n'
                                'invalid command\nERROR: unrecognized command\n\n'
                                'write\nERROR: syntax: write <path> <some_text>\n\n'
                                'help' + get_help() + '\n\n'
                                'help ls\nsyntax: ls <optional_path>\n\n'
                                'help invalid_command' + get_help() + '\n\n')

    def test_commands_1(self):
        expected = [
            ("cd /home", "foo_sender@zulip.com:\nERROR: invalid path"),
            ("mkdir home", "foo_sender@zulip.com:\ndirectory created"),
            ("pwd", "foo_sender@zulip.com:\n/"),
            ("help", self.help_txt),
            ("help ls", "foo_sender@zulip.com:\nsyntax: ls <optional_path>"),
            ("", self.help_txt),
        ]
        self.check_expected_responses(expected)

    def test_commands_2(self):
        expected = [
            ("sample_conversation", "foo_sender@zulip.com:\n" + self.sample_conversation_text),
            ("help", self.help_txt),
            ("help ls", "foo_sender@zulip.com:\nsyntax: ls <optional_path>"),
            ("", self.help_txt),
            ("pwd", "foo_sender@zulip.com:\n/"),
            ("cd /home", "foo_sender@zulip.com:\nERROR: invalid path"),
            ("mkdir home", "foo_sender@zulip.com:\ndirectory created"),
            ("cd /home", "foo_sender@zulip.com:\nCurrent path: /home/"),
        ]
        self.check_expected_responses(expected)

    def test_commands_3(self):
        expected = [
            ('cd /', 'foo_sender@zulip.com:\nCurrent path: /'),
            ('cd /home', 'foo_sender@zulip.com:\nERROR: invalid path'),
            ('cd .', 'foo_sender@zulip.com:\nERROR: invalid path'),
            ('mkdir home', 'foo_sender@zulip.com:\ndirectory created'),
            ('cd home', 'foo_sender@zulip.com:\nCurrent path: /home/'),
            ('cd /home/', 'foo_sender@zulip.com:\nCurrent path: /home/'),
            ('mkdir stuff/', 'foo_sender@zulip.com:\nERROR: stuff/ is not a valid name'),
            ('mkdir stuff', 'foo_sender@zulip.com:\ndirectory created'),
            ('write stuff/file1 something', 'foo_sender@zulip.com:\nfile written'),
            ('read stuff/file1', 'foo_sender@zulip.com:\nsomething'),
            ('read /home/stuff/file1', 'foo_sender@zulip.com:\nsomething'),
            ('read home/stuff/file1', 'foo_sender@zulip.com:\nERROR: file does not exist'),
            ('pwd    ', 'foo_sender@zulip.com:\n/home/'),
            ('pwd bla', 'foo_sender@zulip.com:\nERROR: syntax: pwd'),
            ('ls bla foo', 'foo_sender@zulip.com:\nERROR: syntax: ls <optional_path>'),
            ('cd /', 'foo_sender@zulip.com:\nCurrent path: /'),
            ('rm home', 'foo_sender@zulip.com:\nERROR: /home/ is a directory, file required'),
            ('rmdir home', 'foo_sender@zulip.com:\nremoved'),
            ('ls  ', 'foo_sender@zulip.com:\nWARNING: directory is empty'),
            ('cd home', 'foo_sender@zulip.com:\nERROR: invalid path'),
            ('read /home/stuff/file1', 'foo_sender@zulip.com:\nERROR: file does not exist'),
            ('cd /', 'foo_sender@zulip.com:\nCurrent path: /'),
            ('write /foo contents of /foo', 'foo_sender@zulip.com:\nfile written'),
            ('read /foo', 'foo_sender@zulip.com:\ncontents of /foo'),
            ('write /bar Contents: bar bar', 'foo_sender@zulip.com:\nfile written'),
            ('read /bar', 'foo_sender@zulip.com:\nContents: bar bar'),
            ('write /bar invalid', 'foo_sender@zulip.com:\nERROR: file already exists'),
            ('rm /bar', 'foo_sender@zulip.com:\nremoved'),
            ('rm /bar', 'foo_sender@zulip.com:\nERROR: file does not exist'),
            ('write /bar new bar', 'foo_sender@zulip.com:\nfile written'),
            ('read /bar', 'foo_sender@zulip.com:\nnew bar'),
            ('write /yo/invalid whatever', 'foo_sender@zulip.com:\nERROR: /yo is not a directory'),
            ('mkdir /yo', 'foo_sender@zulip.com:\ndirectory created'),
            ('read /yo', 'foo_sender@zulip.com:\nERROR: /yo/ is a directory, file required'),
            ('ls /yo', 'foo_sender@zulip.com:\nWARNING: directory is empty'),
            ('read /yo/nada', 'foo_sender@zulip.com:\nERROR: file does not exist'),
            ('write /yo whatever', 'foo_sender@zulip.com:\nERROR: file already exists'),
            ('rmdir /yo/whatever/this', 'foo_sender@zulip.com:\nERROR: directory does not exist'),
            ('write /yo/apple red', 'foo_sender@zulip.com:\nfile written'),
            ('read /yo/apple', 'foo_sender@zulip.com:\nred'),
            ('rmdir /yo/apple', 'foo_sender@zulip.com:\nERROR: /yo/*apple* is a file, directory required'),
            ('cd /yo/apple', 'foo_sender@zulip.com:\nERROR: /yo/*apple* is a file, directory required'),
            ('mkdir /yo/apple', 'foo_sender@zulip.com:\nERROR: file already exists'),
            ('ls /invalid', 'foo_sender@zulip.com:\nERROR: file does not exist'),
            ('ls /foo', 'foo_sender@zulip.com:\nERROR: /foo is not a directory'),
            ('ls /', 'foo_sender@zulip.com:\n* /*bar*\n* /*foo*\n* /yo/'),
            ('invalid command', 'foo_sender@zulip.com:\nERROR: unrecognized command'),
            ('write', 'foo_sender@zulip.com:\nERROR: syntax: write <path> <some_text>'),
            ('help', self.help_txt),
            ('help ls', 'foo_sender@zulip.com:\nsyntax: ls <optional_path>'),
            ('help invalid_command', self.help_txt),
        ]
        self.check_expected_responses(expected)

from zulip_bots.test_lib import BotTestCase
from zulip_bots.bots.virtual_fs.virtual_fs import sample_conversation
from unittest.mock import patch

class TestVirtualFsBot(BotTestCase):
    bot_name = "virtual_fs"
    help_txt = ('foo@example.com:\n\nThis bot implements a virtual file system for a stream.\n'
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

    def test_multiple_recipient_conversation(self) -> None:
        expected = [
            ("mkdir home", "foo@example.com:\ndirectory created"),
        ]
        message = dict(
            display_recipient=[{'email': 'foo@example.com'}, {'email': 'boo@example.com'}],
            sender_email='foo@example.com',
            sender_full_name='Foo Test User',
            sender_id='123',
            content="mkdir home",
        )
        with patch('zulip_bots.test_lib.BotTestCase.make_request_message', return_value=message):
            self.verify_dialog(expected)

    def test_sample_conversation_help(self) -> None:
        # There's nothing terribly tricky about the "sample conversation,"
        # so we just do a quick sanity check.
        reply = self.get_reply_dict('sample_conversation')
        content = reply['content']
        frag = 'foo@example.com:\ncd /\nCurrent path: /\n\n'
        self.assertTrue(content.startswith(frag))
        frag = 'read home/stuff/file1\nERROR: file does not exist\n\n'
        self.assertIn(frag, content)

    def test_sample_conversation(self) -> None:
        # The function sample_conversation is actually part of the
        # bot's implementation, because we render a sample conversation
        # for the user's benefit if they ask.  But then we can also
        # use it to test that the bot works as advertised.
        expected = [
            (request, 'foo@example.com:\n' + reply)
            for (request, reply)
            in sample_conversation()
        ]
        self.verify_dialog(expected)

    def test_commands_1(self) -> None:
        expected = [
            ("cd /home", "foo@example.com:\nERROR: invalid path"),
            ("mkdir home", "foo@example.com:\ndirectory created"),
            ("pwd", "foo@example.com:\n/"),
            ("help", self.help_txt),
            ("help ls", "foo@example.com:\nsyntax: ls <optional_path>"),
            ("", self.help_txt),
        ]
        self.verify_dialog(expected)

    def test_commands_2(self) -> None:
        expected = [
            ("help", self.help_txt),
            ("help ls", "foo@example.com:\nsyntax: ls <optional_path>"),
            ("help invalid", self.help_txt),
            ("", self.help_txt),
            ("write test hello world", "foo@example.com:\nfile written"),
            ("rmdir test", "foo@example.com:\nERROR: /*test* is a file, directory required"),
            ("cd test", "foo@example.com:\nERROR: /*test* is a file, directory required"),
            ("mkdir /foo/boo", "foo@example.com:\nERROR: /foo is not a directory"),
            ("pwd", "foo@example.com:\n/"),
            ("cd /home", "foo@example.com:\nERROR: invalid path"),
            ("mkdir etc", "foo@example.com:\ndirectory created"),
            ("mkdir home", "foo@example.com:\ndirectory created"),
            ("cd /home", "foo@example.com:\nCurrent path: /home/"),
            ("write test hello world", "foo@example.com:\nfile written"),
            ("rm test", "foo@example.com:\nremoved"),
            ("mkdir steve", "foo@example.com:\ndirectory created"),
            ("rmdir /home", "foo@example.com:\nremoved"),
            ("pwd", "foo@example.com:\nERROR: the current directory does not exist"),
            ("ls", "foo@example.com:\nERROR: file does not exist"),
            ("ls foo/", "foo@example.com:\nERROR: foo/ is not a valid name"),
            ("rm foo/", "foo@example.com:\nERROR: foo/ is not a valid name"),
            ("rmdir foo/", "foo@example.com:\nERROR: foo/ is not a valid name"),
            ("write foo/ a", "foo@example.com:\nERROR: foo/ is not a valid name"),
            ("read foo/", "foo@example.com:\nERROR: foo/ is not a valid name"),
            ("rmdir /foo", "foo@example.com:\nERROR: directory does not exist"),
        ]
        self.verify_dialog(expected)

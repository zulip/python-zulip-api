from typing import Any, Dict, Optional

from zulip_bots.test_lib import BotTestCase, DefaultTests

class TestFrontBot(BotTestCase, DefaultTests):
    bot_name = 'front'

    def make_request_message(self, content: str) -> Dict[str, Any]:
        message = super().make_request_message(content)
        message['subject'] = "cnv_kqatm2"
        message['sender_email'] = "leela@planet-express.com"
        return message

    def test_bot_invalid_api_key(self) -> None:
        invalid_api_key = ''
        with self.mock_config_info({'api_key': invalid_api_key}):
            with self.assertRaises(KeyError):
                bot, bot_handler = self._get_handlers()

    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info({'api_key': "TEST"}):
            self.verify_reply("", "Unknown command. Use `help` for instructions.")

    def test_help(self) -> None:
        with self.mock_config_info({'api_key': "TEST"}):
            self.verify_reply('help', "`archive` Archive a conversation.\n"
                                      "`delete` Delete a conversation.\n"
                                      "`spam` Mark a conversation as spam.\n"
                                      "`open` Restore a conversation.\n"
                                      "`comment <text>` Leave a comment.\n")

    def test_archive(self) -> None:
        with self.mock_config_info({'api_key': "TEST"}):
            with self.mock_http_conversation('archive'):
                self.verify_reply('archive', "Conversation was archived.")

    def test_archive_error(self) -> None:
        self._test_command_error('archive')

    def test_delete(self) -> None:
        with self.mock_config_info({'api_key': "TEST"}):
            with self.mock_http_conversation('delete'):
                self.verify_reply('delete', "Conversation was deleted.")

    def test_delete_error(self) -> None:
        self._test_command_error('delete')

    def test_spam(self) -> None:
        with self.mock_config_info({'api_key': "TEST"}):
            with self.mock_http_conversation('spam'):
                self.verify_reply('spam', "Conversation was marked as spam.")

    def test_spam_error(self) -> None:
        self._test_command_error('spam')

    def test_restore(self) -> None:
        with self.mock_config_info({'api_key': "TEST"}):
            with self.mock_http_conversation('open'):
                self.verify_reply('open', "Conversation was restored.")

    def test_restore_error(self) -> None:
        self._test_command_error('open')

    def test_comment(self) -> None:
        body = "@bender, I thought you were supposed to be cooking for this party."
        with self.mock_config_info({'api_key': "TEST"}):
            with self.mock_http_conversation('comment'):
                self.verify_reply("comment " + body, "Comment was sent.")

    def test_comment_error(self) -> None:
        body = "@bender, I thought you were supposed to be cooking for this party."
        self._test_command_error('comment', body)

    def _test_command_error(self, command_name: str, command_arg: Optional[str] = None) -> None:
        bot_command = command_name
        if command_arg:
            bot_command += ' {}'.format(command_arg)
        with self.mock_config_info({'api_key': "TEST"}):
            with self.mock_http_conversation('{}_error'.format(command_name)):
                self.verify_reply(bot_command, 'Something went wrong.')


class TestFrontBotWrongTopic(BotTestCase, DefaultTests):
    bot_name = 'front'

    def make_request_message(self, content: str) -> Dict[str, Any]:
        message = super().make_request_message(content)
        message['subject'] = "kqatm2"
        return message

    def test_bot_responds_to_empty_message(self) -> None:
        pass

    def test_no_conversation_id(self) -> None:
        with self.mock_config_info({'api_key': "TEST"}):
            self.verify_reply('archive', "No coversation ID found. Please make "
                                         "sure that the name of the topic "
                                         "contains a valid coversation ID.")

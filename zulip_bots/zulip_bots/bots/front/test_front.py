from typing import Any, Dict

from zulip_bots.test_lib import BotTestCase

class TestFrontBot(BotTestCase):
    bot_name = 'front'

    def make_request_message(self, content: str) -> Dict[str, Any]:
        message = super().make_request_message(content)
        message['subject'] = "cnv_kqatm2"
        message['sender_email'] = "leela@planet-express.com"
        return message

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

    def test_delete(self) -> None:
        with self.mock_config_info({'api_key': "TEST"}):
            with self.mock_http_conversation('delete'):
                self.verify_reply('delete', "Conversation was deleted.")

    def test_spam(self) -> None:
        with self.mock_config_info({'api_key': "TEST"}):
            with self.mock_http_conversation('spam'):
                self.verify_reply('spam', "Conversation was marked as spam.")

    def test_restore(self) -> None:
        with self.mock_config_info({'api_key': "TEST"}):
            with self.mock_http_conversation('open'):
                self.verify_reply('open', "Conversation was restored.")

    def test_comment(self) -> None:
        body = "@bender, I thought you were supposed to be cooking for this party."
        with self.mock_config_info({'api_key': "TEST"}):
            with self.mock_http_conversation('comment'):
                self.verify_reply("comment " + body, "Comment was sent.")

class TestFrontBotWrongTopic(BotTestCase):
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

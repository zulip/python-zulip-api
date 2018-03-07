from unittest.mock import patch
from zulip_bots.test_lib import BotTestCase
from requests.exceptions import ConnectionError

class TestFlockBot(BotTestCase):
    bot_name = "flock"
    normal_config = {"token": "12345"}

    message_config = {
        "token": "12345",
        "text": "Ricky: test message",
        "to": "u:somekey"
    }

    help_message = '''
You can send messages to any Flock user associated with your account from Zulip.
*Syntax*: **@botname to: message** where `to` is **firstName** of recipient.
'''

    def test_bot_responds_to_empty_message(self) -> None:
        self.verify_reply('', self.help_message)

    def test_help_message(self) -> None:
        self.verify_reply('', self.help_message)

    def test_fetch_id_connection_error(self) -> None:
        with self.mock_config_info(self.normal_config), \
                patch('requests.get', side_effect=ConnectionError()), \
                patch('logging.exception'):
            self.verify_reply('tyler: Hey tyler', "Uh-Oh, couldn\'t process the request \
right now.\nPlease try again later")

    def test_response_connection_error(self) -> None:
        with self.mock_config_info(self.message_config), \
                patch('requests.get', side_effect=ConnectionError()), \
                patch('logging.exception'):
            self.verify_reply('Ricky: test message', "Uh-Oh, couldn\'t process the request \
right now.\nPlease try again later")

    @patch('zulip_bots.bots.flock.flock.find_recipient')
    def test_no_recipient_found(self, find_recipient: str) -> None:
        bot_response = "No user found. Make sure you typed it correctly."
        find_recipient.return_value = None
        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_no_recipient_found'):
                    self.verify_reply('david: hello', bot_response)

    @patch('zulip_bots.bots.flock.flock.get_recipient_id')
    def test_message_send_success(self, get_recipient_id: str) -> None:
        bot_response = "Message sent."
        get_recipient_id.return_value = "u:userid"
        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_message_send_success'):
                    self.verify_reply('Rishabh: hi there', bot_response)

    @patch('zulip_bots.bots.flock.flock.get_recipient_id')
    def test_message_send_failed(self, get_recipient_id: str) -> None:
        bot_response = "Message sending failed :slightly_frowning_face:. Please try again."
        get_recipient_id.return_value = "u:invalid"
        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_message_send_failed'):
                    self.verify_reply('Rishabh: hi there', bot_response)

from unittest.mock import patch, Mock
from zulip_bots.test_lib import StubBotHandler, BotTestCase, get_bot_message_handler
from requests.exceptions import ConnectionError

class TestBeeminderBot(BotTestCase):
    bot_name = "beeminder"
    normal_config  = {
        "auth_token": "XXXXXX",
        "username": "aaron",
        "goalname": "goal"
    }

    help_message = '''
You can add datapoints towards your beeminder goals \
following the syntax shown below :smile:.\n \
\n**@mention-botname daystamp, value, comment**\
\n* `daystamp`**:** *yyyymmdd*  \
[**NOTE:** Optional field, default is *current daystamp*],\
\n* `value`**:** Enter a value [**NOTE:** Required field, can be any number],\
\n* `comment`**:** Add a comment [**NOTE:** Optional field, default is *None*]\
'''

    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_blank_input'):
                    self.verify_reply('', self.help_message)

    def test_help_message(self) -> None:
        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_help_message'):
                    self.verify_reply('help', self.help_message)

    def test_normal(self) -> None:
        bot_response = '[Datapoint](https://www.beeminder.com/aaron/goal) created.'
        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_normal'):
            self.verify_reply('2, hi there!', bot_response)

    def test_syntax_error(self) -> None:
        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_syntax_error'):
                    bot_response = "Make sure you follow the syntax.\n You can take a look \
at syntax by: @mention-botname help"
                    self.verify_reply("20180303, 50, comment, redundant comment", bot_response)

    def test_connection_error(self) -> None:
        with self.mock_config_info(self.normal_config), \
                patch('requests.post', side_effect=ConnectionError()), \
                patch('logging.exception'):
            self.verify_reply('?$!', 'Uh-Oh, couldn\'t process the request \
right now.\nPlease try again later')

    def test_error(self) -> None:
        bot_request = 'notNumber'
        bot_response = "Error occured : 422"
        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_error'):
                    self.verify_reply(bot_request, bot_response)

    def test_invalid(self) -> None:
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        with self.mock_config_info({'auth_token': 'someInvalidKey',
                                    'username': 'aaron',
                                    'goalname': 'goal',
                                    "value": "5"}), \
                self.mock_http_conversation('test_invalid'), \
                self.assertRaises(bot_handler.BotQuitException):
                    bot.initialize(bot_handler)

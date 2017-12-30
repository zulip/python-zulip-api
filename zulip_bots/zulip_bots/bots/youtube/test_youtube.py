from unittest.mock import patch
from requests.exceptions import HTTPError, ConnectionError

from zulip_bots.test_lib import StubBotHandler, BotTestCase, get_bot_message_handler
from typing import Any, Union, Dict
class TestYoutubeBot(BotTestCase):
    bot_name = "youtube"
    normal_config  = {'key': '12345678',
                      'number_of_results': '5',
                      'video_region': 'US'}  # type: Dict[str,str]

    help_content = "*Help for YouTube bot* :robot_face: : \n\n" \
                   "The bot responds to messages starting with @mention-bot.\n\n" \
                   "`@mention-bot <search terms>` will return top Youtube video for the given `<search term>`.\n" \
                   "`@mention-bot top <search terms>` also returns the top Youtube result.\n" \
                   "`@mention-bot list <search terms>` will return a list Youtube videos for the given <search term>.\n \n" \
                   "Example:\n" \
                   " * @mention-bot funny cats\n" \
                   " * @mention-bot list funny dogs"

    # Override default function in BotTestCase
    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_keyok'):
                    self.verify_reply('', self.help_content)

    def test_single(self) -> None:
        bot_response = 'Here is what I found for `funny cats` : \n'\
                       'Cats are so funny you will die laughing - ' \
                       'Funny cat compilation - [Watch now](https://www.youtube.com/watch?v=5dsGWM5XGdg)'

        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_single'):
                    self.verify_reply('funny cats', bot_response)

    def test_invalid_key(self) -> None:
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        with self.mock_config_info({'key': 'somethinginvalid', 'number_of_results': '5', 'video_region': 'US'}), \
                self.mock_http_conversation('test_invalid_key'), \
                self.assertRaises(bot_handler.BotQuitException):
                    bot.initialize(bot_handler)

    def test_multiple(self) -> None:
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        bot_response = 'Here is what I found for `marvel` : ' \
                       '\n * Marvel Studios\' Avengers: Infinity War Official Trailer - [Watch now](https://www.youtube.com/watch/6ZfuNTqbHE8)' \
                       '\n * Marvel Studios\' Black Panther - Official Trailer - [Watch now](https://www.youtube.com/watch/xjDjIWPwcPU)' \
                       '\n * MARVEL RISING BEGINS! | The Next Generation of Marvel Heroes (EXCLUSIVE) - [Watch now](https://www.youtube.com/watch/6HTPCTtkWoA)' \
                       '\n * Marvel Contest of Champions Taskmaster Spotlight - [Watch now](https://www.youtube.com/watch/-8uqxdcJ9WM)' \
                       '\n * 5* Crystal Opening! SO LUCKY! - Marvel Contest Of Champions - [Watch now](https://www.youtube.com/watch/l7rrsGKJ_O4)'

        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_multiple'):
                    self.verify_reply('list marvel', bot_response)

    def test_noresult(self) -> None:
        bot_response = 'Oops ! Sorry I couldn\'t find any video for  `somethingrandomwithnoresult` ' \
                       ':slightly_frowning_face:'

        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_noresult'):
            self.verify_reply('somethingrandomwithnoresult', bot_response,)

    def test_help(self) -> None:
        help_content = self.help_content
        with self.mock_config_info(self.normal_config), \
                self.mock_http_conversation('test_keyok'):
                    self.verify_reply('help', help_content)
                    self.verify_reply('list', help_content)
                    self.verify_reply('help list', help_content)
                    self.verify_reply('top', help_content)

    def test_connection_error(self) -> None:
        with self.mock_config_info(self.normal_config), \
                patch('requests.get', side_effect=ConnectionError()), \
                patch('logging.exception'):
            self.verify_reply('Wow !', 'Uh-Oh, couldn\'t process the request '
                              'right now.\nPlease again later')

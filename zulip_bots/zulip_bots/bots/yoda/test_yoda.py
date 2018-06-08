from zulip_bots.bots.yoda.yoda import ServiceUnavailableError
from zulip_bots.test_lib import BotTestCase, DefaultTests

from typing import Optional

class TestYodaBot(BotTestCase, DefaultTests):
    bot_name = "yoda"

    help_text = '''
            This bot allows users to translate a sentence into
            'Yoda speak'.
            Users should preface messages with '@mention-bot'.

            Before running this, make sure to get a Mashape Api token.
            Instructions are in the 'readme.md' file.
            Store it in the 'yoda.conf' file.
            The 'yoda.conf' file should be located in this bot's (zulip_bots/bots/yoda/yoda)
            directory.
            Example input:
            @mention-bot You will learn how to speak like me someday.
            '''

    def _test(self, message: str, response: str, fixture: Optional[str]=None) -> None:
        with self.mock_config_info({'api_key': '12345678'}):
            if fixture is not None:
                with self.mock_http_conversation(fixture):
                    self.verify_reply(message, response)
            else:
                self.verify_reply(message, response)

    # Override default function in BotTestCase
    def test_bot_responds_to_empty_message(self) -> None:
        self._test('', self.help_text)

    def test_bot(self) -> None:
        # Test normal sentence (1).
        self._test('You will learn how to speak like me someday.',
                   "Learn how to speak like me someday, you will. Yes, hmmm.",
                   'test_1')

        # Test normal sentence (2).
        self._test('you still have much to learn',
                   "Much to learn, you still have.",
                   'test_2')

        # Test only numbers.
        self._test('23456', "23456.  Herh herh herh.",
                   'test_only_numbers')

        # Test help.
        self._test('help', self.help_text)

        # Test invalid input.
        self._test('@#$%^&*',
                   "Invalid input, please check the sentence you have entered.",
                   'test_invalid_input')

        # Test 403 response.
        self._test('You will learn how to speak like me someday.',
                   "Invalid Api Key. Did you follow the instructions in the `readme.md` file?",
                   'test_api_key_error')

        # Test 503 response.
        with self.assertRaises(ServiceUnavailableError):
            self._test('You will learn how to speak like me someday.',
                       "The service is temporarily unavailable, please try again.",
                       'test_service_unavailable_error')

        # Test unknown response.
        self._test('You will learn how to speak like me someday.',
                   "Unknown Error.Error code: 123 Did you follow the instructions in the `readme.md` file?",
                   'test_unknown_error')

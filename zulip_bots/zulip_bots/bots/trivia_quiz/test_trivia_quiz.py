import json
import html

from unittest.mock import patch
from typing import Optional

from zulip_bots.test_lib import (
    BotTestCase,
    DefaultTests,
    read_bot_fixture_data,
)

from zulip_bots.request_test_lib import (
    mock_request_exception,
)

from zulip_bots.bots.trivia_quiz.trivia_quiz import (
    get_quiz_from_payload,
    fix_quotes,
)

class TestTriviaQuizBot(BotTestCase, DefaultTests):
    bot_name = "trivia_quiz"  # type: str

    new_question_response = '\nQ: Which class of animals are newts members of?\n\n' + \
        '* **A** Amphibian\n' + \
        '* **B** Fish\n' + \
        '* **C** Reptiles\n' + \
        '* **D** Mammals\n' + \
        '**reply**: answer Q001 <letter>'

    def _test(self, message: str, response: str, fixture: Optional[str]=None) -> None:
        if fixture:
            with self.mock_http_conversation(fixture):
                self.verify_reply(message, response)
        else:
            self.verify_reply(message, response)

    def test_bot_responds_to_empty_message(self) -> None:
        self._test('', 'type "new" for a new question')

    def test_bot_new_question(self) -> None:
        with patch('random.shuffle'):
            self._test('new', self.new_question_response, 'test_new_question')

    def test_question_not_available(self) -> None:
        self._test('new', 'Uh-Oh! Trivia service is down.', 'test_status_code')

        with mock_request_exception():
            self.verify_reply('new', 'Uh-Oh! Trivia service is down.')

    def test_fix_quotes(self) -> None:
        self.assertEqual(fix_quotes('test &amp; test'), html.unescape('test &amp; test'))
        print('f')
        with patch('html.unescape') as mock_html_unescape:
            mock_html_unescape.side_effect = Exception
            with self.assertRaises(Exception) as exception:
                fix_quotes('test')
            self.assertEqual(str(exception.exception), "Please use python3.4 or later for this bot.")

    def test_invalid_answer(self) -> None:
        invalid_replies = ['answer A',
                           'answer A Q10',
                           'answer Q001 K',
                           'answer 001 A']
        for reply in invalid_replies:
            self._test(reply, 'Invalid answer format')

    def test_invalid_quiz_id(self) -> None:
        self._test('answer Q100 A', 'Invalid quiz id')

    def test_answers(self) -> None:
        quiz_payload = read_bot_fixture_data('trivia_quiz', 'test_new_question')['response']
        with patch('random.shuffle'):
            quiz = get_quiz_from_payload(quiz_payload)

        self.assertEqual(quiz['question'], 'Which class of animals are newts members of?')
        self.assertEqual(quiz['correct_letter'], 'A')
        self.assertEqual(quiz['answers']['D'], 'Mammals')

        # test incorrect answer
        with patch('zulip_bots.bots.trivia_quiz.trivia_quiz.get_quiz_from_id',
                   return_value=json.dumps(quiz)):
            self._test('answer Q001 B', '**WRONG!** B is not correct :disappointed:')

        # test correct answer
        with patch('zulip_bots.bots.trivia_quiz.trivia_quiz.get_quiz_from_id',
                   return_value=json.dumps(quiz)):
            with patch('zulip_bots.bots.trivia_quiz.trivia_quiz.start_new_quiz') as mock_new_quiz:
                self._test('answer Q001 A', '**CORRECT!** Amphibian :tada:')

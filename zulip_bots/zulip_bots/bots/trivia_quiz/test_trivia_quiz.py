import json

from unittest.mock import patch
from typing import Optional

from zulip_bots.test_lib import (
    BotTestCase,
    read_bot_fixture_data,
)

from zulip_bots.bots.trivia_quiz.trivia_quiz import (
    get_quiz_from_payload,
)

class TestTriviaQuizBot(BotTestCase):
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

import json
from typing import Any, Dict, Optional, Tuple
from unittest.mock import patch

from typing_extensions import override

from zulip_bots.bots.trivia_quiz.trivia_quiz import (
    get_quiz_from_id,
    get_quiz_from_payload,
    handle_answer,
    update_quiz,
)
from zulip_bots.request_test_lib import mock_request_exception
from zulip_bots.test_file_utils import read_bot_fixture_data
from zulip_bots.test_lib import BotTestCase, DefaultTests, StubBotHandler


class TestTriviaQuizBot(BotTestCase, DefaultTests):
    bot_name: str = "trivia_quiz"

    new_question_response = (
        "\nQ: Which class of animals are newts members of?\n\n"
        "* **A** Amphibian\n"
        "* **B** Fish\n"
        "* **C** Reptiles\n"
        "* **D** Mammals\n"
        "**reply**: answer Q001 <letter>"
    )

    def get_test_quiz(self) -> Tuple[Dict[str, Any], Any]:
        bot_handler = StubBotHandler()
        quiz_payload = read_bot_fixture_data("trivia_quiz", "test_new_question")["response"]
        with patch("random.shuffle"):
            quiz = get_quiz_from_payload(quiz_payload)
        return quiz, bot_handler

    def _test(self, message: str, response: str, fixture: Optional[str] = None) -> None:
        if fixture:
            with self.mock_http_conversation(fixture):
                self.verify_reply(message, response)
        else:
            self.verify_reply(message, response)

    @override
    def test_bot_responds_to_empty_message(self) -> None:
        self._test("", 'type "new" for a new question')

    def test_bot_new_question(self) -> None:
        with patch("random.shuffle"):
            self._test("new", self.new_question_response, "test_new_question")

    def test_question_not_available(self) -> None:
        self._test("new", "Uh-Oh! Trivia service is down.", "test_status_code")

        with mock_request_exception():
            self.verify_reply("new", "Uh-Oh! Trivia service is down.")

    def test_invalid_answer(self) -> None:
        invalid_replies = ["answer A", "answer A Q10", "answer Q001 K", "answer 001 A"]
        for reply in invalid_replies:
            self._test(reply, "Invalid answer format")

    def test_invalid_quiz_id(self) -> None:
        self._test("answer Q100 A", "Invalid quiz id")

    def test_answers(self) -> None:
        quiz_payload = read_bot_fixture_data("trivia_quiz", "test_new_question")["response"]
        with patch("random.shuffle"):
            quiz = get_quiz_from_payload(quiz_payload)

        # Test initial storage
        self.assertEqual(quiz["question"], "Which class of animals are newts members of?")
        self.assertEqual(quiz["correct_letter"], "A")
        self.assertEqual(quiz["answers"]["D"], "Mammals")
        self.assertEqual(quiz["answered_options"], [])
        self.assertEqual(quiz["pending"], True)

        # test incorrect answer
        with patch(
            "zulip_bots.bots.trivia_quiz.trivia_quiz.get_quiz_from_id",
            return_value=json.dumps(quiz),
        ):
            self._test("answer Q001 B", ":disappointed: WRONG, Foo Test User! B is not correct.")

        # test correct answer
        with patch(
            "zulip_bots.bots.trivia_quiz.trivia_quiz.get_quiz_from_id",
            return_value=json.dumps(quiz),
        ):
            with patch("zulip_bots.bots.trivia_quiz.trivia_quiz.start_new_quiz"):
                self._test("answer Q001 A", ":tada: **Amphibian** is correct, Foo Test User!")

    def test_update_quiz(self) -> None:
        quiz, bot_handler = self.get_test_quiz()
        update_quiz(quiz, "Q001", bot_handler)
        test_quiz = json.loads(bot_handler.storage.get("Q001"))
        self.assertEqual(test_quiz, quiz)

    def test_get_quiz_from_id(self) -> None:
        quiz, bot_handler = self.get_test_quiz()
        bot_handler.storage.put("Q001", quiz)
        self.assertEqual(get_quiz_from_id("Q001", bot_handler), quiz)

    def test_handle_answer(self) -> None:
        quiz, bot_handler = self.get_test_quiz()
        # create test initial storage
        update_quiz(quiz, "Q001", bot_handler)

        # test for a correct answer
        start_new_question, response = handle_answer(quiz, "A", "Q001", bot_handler, "Test user")
        self.assertTrue(start_new_question)
        self.assertEqual(response, ":tada: **Amphibian** is correct, Test user!")

        # test for an incorrect answer
        start_new_question, response = handle_answer(quiz, "D", "Q001", bot_handler, "Test User")
        self.assertFalse(start_new_question)
        self.assertEqual(response, ":disappointed: WRONG, Test User! D is not correct.")

    def test_handle_answer_three_failed_attempts(self) -> None:
        quiz, bot_handler = self.get_test_quiz()
        # create test storage for a question which has been incorrectly answered twice
        quiz["answered_options"] = ["C", "B"]
        update_quiz(quiz, "Q001", bot_handler)

        # test response  and storage after three failed attempts
        start_new_question, response = handle_answer(quiz, "D", "Q001", bot_handler, "Test User")
        self.assertEqual(
            response, ":disappointed: WRONG, Test User! The correct answer is **Amphibian**."
        )
        self.assertTrue(start_new_question)
        quiz_reset = json.loads(bot_handler.storage.get("Q001"))
        self.assertEqual(quiz_reset["pending"], False)

        # test response after question has ended
        incorrect_answers = ["B", "C", "D"]
        for ans in incorrect_answers:
            start_new_question, response = handle_answer(
                quiz, ans, "Q001", bot_handler, "Test User"
            )
            self.assertEqual(
                response, ":disappointed: WRONG, Test User! The correct answer is **Amphibian**."
            )
            self.assertFalse(start_new_question)
        start_new_question, response = handle_answer(quiz, "A", "Q001", bot_handler, "Test User")
        self.assertEqual(response, ":tada: **Amphibian** is correct, Test User!")
        self.assertFalse(start_new_question)

        # test storage after question has ended
        quiz_reset = json.loads(bot_handler.storage.get("Q001"))
        self.assertEqual(quiz_reset["pending"], False)

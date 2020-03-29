import json

from unittest.mock import patch

from zulip_bots.test_lib import (
    BotTestCase,
    DefaultTests,
    read_bot_fixture_data,
)

from zulip_bots.request_test_lib import (
    mock_request_exception
)

from zulip_bots.bots.trivia_quiz_game.controller import (
    TriviaQuizGameModel,
    NotAvailableException
)

from zulip_bots.bots.trivia_quiz_game.trivia_quiz_game import (
    TriviaQuizGameMessageHandler
)

from zulip_bots.game_handler import BadMoveException

class TestTriviaQuizGameBot(BotTestCase, DefaultTests):
    bot_name = 'trivia_quiz_game'  # type: str

    new_question_response = '\nQ: Which class of animals are newts members of?\n\n' + \
        '* **A** Amphibian\n' + \
        '* **B** Fish\n' + \
        '* **C** Reptiles\n' + \
        '* **D** Mammals\n' + \
        '**reply**: <letter>'

    test_question = {
        'question': 'Question 1?',
        'answers': {
            'A': 'Correct',
            'B': 'Incorrect 1',
            'C': 'Incorrect 2',
            'D': 'Incorrect 3'
        },
        'correct_letter': 'A'
    }

    test_question_message_content = '''
Q: Question 1?

* **A** Correct
* **B** Incorrect 1
* **C** Incorrect 2
* **D** Incorrect 3
**reply**: <letter>'''

    test_question_message_widget = '{"widget_type": "zform", "extra_data": {"type": "choices", "heading": "Question 1?", "choices": [{"type": "multiple_choice", "short_name": "A", "long_name": "Correct", "reply": "A"}, {"type": "multiple_choice", "short_name": "B", "long_name": "Incorrect 1", "reply": "B"}, {"type": "multiple_choice", "short_name": "C", "long_name": "Incorrect 2", "reply": "C"}, {"type": "multiple_choice", "short_name": "D", "long_name": "Incorrect 3", "reply": "D"}]}}'

    def test_question_not_available(self) -> None:
        with self.mock_http_conversation('test_new_question'):
            model = TriviaQuizGameModel()
        # Exception
        with self.assertRaises(NotAvailableException):
            with mock_request_exception():
                model.get_trivia_quiz()
        # non-ok status code
        with self.assertRaises(NotAvailableException):
            with self.mock_http_conversation("test_status_code"):
                model.get_trivia_quiz()

    def test_validate_move(self) -> None:
        with self.mock_http_conversation('test_new_question'):
            model = TriviaQuizGameModel()
        valid_moves = [
            'A',
            'B',
            'C',
            'D'
        ]
        invalid_moves = [
            'AA',
            '1'
        ]
        for valid_move in valid_moves:
            self.assertTrue(model.validate_move(valid_move))
        for invalid_move in invalid_moves:
            self.assertFalse(model.validate_move(invalid_move))

    def test_make_move(self) -> None:
        with self.mock_http_conversation('test_new_question'):
            model = TriviaQuizGameModel()
        model.current_board = self.test_question
        model.scores = {
            0: 0,
            1: 1
        }
        # Invalid move should raise BadMoveException
        with self.assertRaises(BadMoveException):
            model.make_move('AA', 0)
        # Correct move should:
        with self.mock_http_conversation('test_new_question'):
            with patch('random.shuffle'):
                move_data = model.make_move('A', 0)
                # Increment score
                self.assertEqual(model.scores[0], 1)
                # Change question
                self.assertEqual(model.current_board, read_bot_fixture_data("trivia_quiz_game", "test_new_question_dict"))
                # Move data correct should be true
                self.assertTrue(move_data['correct'])
                # Move data score should be the same as model.scores[player_number]
                self.assertEqual(move_data['score'], 1)
        # Incorrect move should:
        with self.mock_http_conversation('test_new_question'):
            model.current_board = self.test_question
            move_data = model.make_move('B', 1)
            # Decrement score
            self.assertEqual(model.scores[1], 0)
            # Move data correct should be false
            self.assertFalse(move_data['correct'])

    def test_determine_game_over(self) -> None:
        with self.mock_http_conversation('test_new_question'):
            model = TriviaQuizGameModel()
            model.scores = {
                0: 0,
                1: 5,
                2: 1
            }
            self.assertEqual(model.determine_game_over(["Test 0", "Test 1", "Test 2"]), "Test 1")
            model.scores = {
                0: 0,
                1: 4,
                2: 1
            }
            self.assertIsNone(model.determine_game_over(["Test 0", "Test 1", "Test 2"]))

    def test_message_handler_parse_board(self) -> None:
        message_handler = TriviaQuizGameMessageHandler()
        board_message_content, board_message_widget = message_handler.parse_board(self.test_question)
        self.assertEqual(board_message_content, self.test_question_message_content)
        self.assertEqual(json.loads(board_message_widget), json.loads(self.test_question_message_widget))

    def test_message_handler_alert_move_message(self) -> None:
        message_handler = TriviaQuizGameMessageHandler()
        correct_responses = [
            (("Test User", "A", {'correct': True, 'score': 5}), ":tada: Correct Test User (5 points)!"),
            (("Test User", "B", {'correct': False, 'score': 1, 'correct_letter': "B"}), ":disappointed: Incorrect Test User (1 points). The correct answer was **B**")
        ]
        for args, response in correct_responses:
            self.assertEqual(message_handler.alert_move_message(*args), response)

    def test_message_handler_get_player_color(self) -> None:
        message_handler = TriviaQuizGameMessageHandler()
        self.assertIsNone(message_handler.get_player_color(0))

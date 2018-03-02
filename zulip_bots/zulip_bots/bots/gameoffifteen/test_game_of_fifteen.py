from zulip_bots.test_lib import BotTestCase

from contextlib import contextmanager
from unittest.mock import MagicMock
from zulip_bots.bots.gameoffifteen.gameoffifteen import *
from zulip_bots.game_handler import BadMoveException
from typing import Dict, Any, List


class TestGameOfFifteenBot(BotTestCase):
    bot_name = 'gameoffifteen'

    def make_request_message(
        self,
        content: str,
        user: str='foo@example.com',
        user_name: str='foo'
    ) -> Dict[str, str]:
        message = dict(
            sender_email=user,
            content=content,
            sender_full_name=user_name
        )
        return message

    # Function that serves similar purpose to BotTestCase.verify_dialog, but allows for multiple responses to be handled
    def verify_response(self, request: str, expected_response: str, response_number: int, user: str='foo@example.com') -> None:
        '''
        This function serves a similar purpose
        to BotTestCase.verify_dialog, but allows
        for multiple responses to be validated,
        and for mocking of the bot's internal data
        '''

        bot, bot_handler = self._get_handlers()
        message = self.make_request_message(request, user)
        bot_handler.reset_transcript()

        bot.handle_message(message, bot_handler)

        responses = [
            message
            for (method, message)
            in bot_handler.transcript
        ]

        first_response = responses[response_number]
        self.assertEqual(expected_response, first_response['content'])

    def help_message(self) -> str:
        return '''** Game of Fifteen Bot Help:**
*Preface all commands with @**test-bot***
* To start a game in a stream, type
`start game`
* To quit a game at any time, type
`quit`
* To see rules of this game, type
`rules`
* To make your move during a game, type
```move <tile1> <tile2> ...```'''

    def test_static_responses(self) -> None:
        self.verify_response('help', self.help_message(), 0)

    def test_game_message_handler_responses(self) -> None:
        board = '\n\n:grey_question::one::two:\n\n:three::four::five:\n\n:six::seven::eight:'
        bot, bot_handler = self._get_handlers()
        self.assertEqual(bot.gameMessageHandler.parse_board(
            self.winning_board), board)
        self.assertEqual(bot.gameMessageHandler.alert_move_message(
            'foo', 'move 1'), 'foo moved 1')
        self.assertEqual(bot.gameMessageHandler.game_start_message(
        ), "Welcome to Game of Fifteen!"
           "To make a move, type @-mention `move <tile1> <tile2> ...`")

    winning_board = [[0, 1, 2],
                     [3, 4, 5],
                     [6, 7, 8]]

    def test_game_of_fifteen_logic(self) -> None:
        def confirmAvailableMoves(
            good_moves: List[int],
            bad_moves: List[int],
            board: List[List[int]]
        ) -> None:
            gameOfFifteenModel.update_board(board)
            for move in good_moves:
                self.assertTrue(gameOfFifteenModel.validate_move(move))

            for move in bad_moves:
                self.assertFalse(gameOfFifteenModel.validate_move(move))

        def confirmMove(
            tile: str,
            token_number: int,
            initial_board: List[List[int]],
            final_board: List[List[int]]
        ) -> None:
            gameOfFifteenModel.update_board(initial_board)
            test_board = gameOfFifteenModel.make_move(
                'move ' + tile, token_number)

            self.assertEqual(test_board, final_board)

        def confirmGameOver(board: List[List[int]], result: str) -> None:
            gameOfFifteenModel.update_board(board)
            game_over = gameOfFifteenModel.determine_game_over(
                ['first_player'])

            self.assertEqual(game_over, result)

        def confirm_coordinates(board: List[List[int]], result: Dict[int, Tuple[int, int]]) -> None:
            gameOfFifteenModel.update_board(board)
            coordinates = gameOfFifteenModel.get_coordinates(board)
            self.assertEqual(coordinates, result)

        gameOfFifteenModel = GameOfFifteenModel()

        # Basic Board setups
        initial_board = [[8, 7, 6],
                         [5, 4, 3],
                         [2, 1, 0]]

        sample_board = [[7, 6, 8],
                        [3, 0, 1],
                        [2, 4, 5]]

        winning_board = [[0, 1, 2],
                         [3, 4, 5],
                         [6, 7, 8]]

        # Test Move Validation Logic
        confirmAvailableMoves([1, 2, 3, 4, 5, 6, 7, 8], [0, 9, -1], initial_board)

        # Test Move Logic
        confirmMove('1', 0, initial_board,
                    [[8, 7, 6],
                     [5, 4, 3],
                     [2, 0, 1]])

        confirmMove('1 2', 0, initial_board,
                    [[8, 7, 6],
                     [5, 4, 3],
                     [0, 2, 1]])

        confirmMove('1 2 5', 0, initial_board,
                    [[8, 7, 6],
                     [0, 4, 3],
                     [5, 2, 1]])

        confirmMove('1 2 5 4', 0, initial_board,
                    [[8, 7, 6],
                     [4, 0, 3],
                     [5, 2, 1]])

        confirmMove('3', 0, sample_board,
                    [[7, 6, 8],
                     [0, 3, 1],
                     [2, 4, 5]])

        confirmMove('3 7', 0, sample_board,
                    [[0, 6, 8],
                     [7, 3, 1],
                     [2, 4, 5]])

        # Test coordinates logic:
        confirm_coordinates(initial_board, {8: (0, 0),
                                            7: (0, 1),
                                            6: (0, 2),
                                            5: (1, 0),
                                            4: (1, 1),
                                            3: (1, 2),
                                            2: (2, 0),
                                            1: (2, 1),
                                            0: (2, 2)})

        # Test Game Over Logic:
        confirmGameOver(winning_board, 'current turn')
        confirmGameOver(sample_board, '')

    def test_invalid_moves(self) -> None:
        model = GameOfFifteenModel()
        move1 = 'move 2'
        move2 = 'move 5'
        move3 = 'move 23'
        move4 = 'move 0'
        move5 = 'move  1  2'
        initial_board = [[8, 7, 6],
                         [5, 4, 3],
                         [2, 1, 0]]

        model.update_board(initial_board)
        with self.assertRaises(BadMoveException):
            model.make_move(move1, player_number=0)
        with self.assertRaises(BadMoveException):
            model.make_move(move2, player_number=0)
        with self.assertRaises(BadMoveException):
            model.make_move(move3, player_number=0)
        with self.assertRaises(BadMoveException):
            model.make_move(move4, player_number=0)
        with self.assertRaises(BadMoveException):
            model.make_move(move5, player_number=0)

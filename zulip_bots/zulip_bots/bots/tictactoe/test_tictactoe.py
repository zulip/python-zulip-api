from zulip_bots.test_lib import BotTestCase
from zulip_bots.game_handler import GameInstance

from tictactoe import TicTacToeModel

from unittest.mock import patch
from typing import List, Tuple, Any



class TestTicTacToeBot(BotTestCase):
    bot_name = 'tictactoe'

    # FIXME: Add tests for computer moves

    # Tests for TicTacToeModel functions
    # Things that might need to be checked: how model is being used in these functions, 
    # When running the tests, many of the failures involved current_board. This 
    # may need to be initialized prior to the constructor initialization in order to 
    # avoid these errors. 

    def test_get_value(self) -> None: 
        board = [[0, 1, 0],
                 [0, 0, 0],
                 [0, 0, 2]]
        position = [0, 1]
        tictactoeboard = TicTacToeModel(board)
        response = 1
        self._test_get_value(tictactoeboard, board, position, response)
    
    def _test_get_value(self, tictactoeboard: TicTacToeModel, board: List[List[int]], position: Tuple[int, int], expected_response: int) -> None:
        response = tictactoeboard.get_value(board, position)
        self.assertEqual(response, expected_response)

    def test_determine_game_over_with_win(self) -> None:
        board = [[1, 1, 1],
                 [0, 2, 0],
                 [2, 0, 2]]
        tictactoeboard = TicTacToeModel(board)
        players = ['Human', 'Computer']
        response = 'current turn'
        self._test_determine_game_over_with_win(tictactoeboard, board, players, response)

    def _test_determine_game_over_with_win(self, tictactoeboard: TicTacToeModel, board: List[List[int]], players: List[str], expected_response: str) -> None:
        
        response = tictactoeboard.determine_game_over(players)
        self.assertEqual(response, expected_response)
    
    def test_determine_game_over_with_draw(self) -> None:
        board = [[1, 2, 1],
                 [1, 2, 1],
                 [2, 1, 2]]
        tictactoeboard = TicTacToeModel(board)
        players = ['Human', 'Computer']
        response = 'draw'
        self._test_determine_game_over_with_draw(tictactoeboard, board, players, response)

    def _test_determine_game_over_with_draw(self, tictactoeboard: TicTacToeModel, board: List[List[int]], players: List[str], expected_response: str) -> None:
        response = tictactoeboard.determine_game_over(players)
        self.assertEqual(response, expected_response)
    
    def test_board_is_full(self) -> None:
        board = [[1, 0, 1],
                 [1, 2, 1],
                 [2, 1, 2]] 
        tictactoeboard = TicTacToeModel(board)
        response = False
        self._test_board_is_full(tictactoeboard, board, response)
    
    def _test_board_is_full(self, tictactoeboard: TicTacToeModel, board: List[List[int]], expected_response: bool) -> None: 
        response = tictactoeboard.board_is_full(board)
        self.assertEqual(response, expected_response)
    
    def test_contains_winning_move(self) -> None:
        board = [[1, 1, 1],
                 [0, 2, 0],
                 [2, 0, 2]]
        tictactoeboard = TicTacToeModel(board)
        response = True
        self._test_contains_winning_move(tictactoeboard, board, response)
    
    def _test_contains_winning_move(self, tictactoeboard: TicTacToeModel, board: List[List[int]], expected_response: bool) -> None:
        response = tictactoeboard.contains_winning_move(board)
        self.assertEqual(response, expected_response)
    

    # def test_tic_tac_toe_model(self) -> None:
    #     board = [[1,2,1],
    #              [2,1,2],
    #              [2,1,2]]

    #     new_model = TicTacToeModel(board)

    #     new_model()

    #     response = ':cross_mark_button: :o_button: :cross_mark_button:\n\n' +\
    #         ':o_button: :cross_mark_button: :o_button:\n\n' +\
    #         ':o_button: :cross_mark_button: :o_button:\n\n'
    #     self._test_computer_moves(board, response)

    # def _test_computer_moves(self, board:List[List[int]], expected_response: str) -> None:
    #     model, message_handler = self._get_game_handlers()
    #     model.board = 
    #     response = model.computer_move(self,board, 1)
    #     self.assertEqual(response, expected_response)
    # FIXME: Add test lib for game_handler


    def test_player_color(self) -> str:
        turn = 0
        response = ':cross_mark_button:'
        self._test_player_color(turn, response)
    
    def _test_player_color(self, turn: int, expected_response: str) -> None:
        model, message_handler = self._get_game_handlers()
        response = message_handler.get_player_color(0)

        self.assertEqual(response, expected_response)
    
    def test_static_responses(self) -> None:
        model, message_handler = self._get_game_handlers()
        self.assertNotEqual(message_handler.get_player_color(0), None)
        self.assertNotEqual(message_handler.game_start_message(), None)
        self.assertEqual(message_handler.alert_move_message(
            'foo', 'move 3'), 'foo put a token at 3')

    def test_has_attributes(self) -> None:
        model, message_handler = self._get_game_handlers()
        self.assertTrue(hasattr(message_handler, 'parse_board') is not None)
        self.assertTrue(
            hasattr(message_handler, 'alert_move_message') is not None)
        self.assertTrue(hasattr(model, 'current_board') is not None)
        self.assertTrue(hasattr(model, 'determine_game_over') is not None)

    def test_parse_board(self) -> None:
        board = [[0, 1, 0],
                 [0, 0, 0],
                 [0, 0, 2]]
        response = ':one: :cross_mark_button: :three:\n\n' +\
            ':four: :five: :six:\n\n' +\
            ':seven: :eight: :o_button:\n\n'
        self._test_parse_board(board, response)

    def _test_parse_board(self, board: List[List[int]], expected_response: str) -> None:
        model, message_handler = self._get_game_handlers()
        response = message_handler.parse_board(board)
        self.assertEqual(response, expected_response)

    def add_user_to_cache(self, name: str, bot: Any=None) -> Any:
        if bot is None:
            bot, bot_handler = self._get_handlers()
        message = {
            'sender_email': '{}@example.com'.format(name),
            'sender_full_name': '{}'.format(name)
        }
        bot.add_user_to_cache(message)
        return bot

    def setup_game(self) -> None:
        bot = self.add_user_to_cache('foo')
        self.add_user_to_cache('baz', bot)
        instance = GameInstance(bot, False, 'test game', 'abc123', [
                                'foo@example.com', 'baz@example.com'], 'test')
        bot.instances.update({'abc123': instance})
        instance.start()
        return bot

    def _get_game_handlers(self) -> Tuple[Any, Any]:
        bot, bot_handler = self._get_handlers()
        return bot.model, bot.gameMessageHandler

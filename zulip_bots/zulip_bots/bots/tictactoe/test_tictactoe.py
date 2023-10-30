from typing import Any, List, Tuple

from zulip_bots.game_handler import GameInstance
from zulip_bots.test_lib import BotTestCase, DefaultTests


class TestTicTacToeBot(BotTestCase, DefaultTests):
    bot_name = "tictactoe"

    # FIXME: Add tests for computer moves
    # FIXME: Add test lib for game_handler

    # Tests for TicTacToeModel functions
    # Things that might need to be checked: how model is being used in these functions,
    # When running the tests, many of the failures involved current_board. This
    # may need to be initialized prior to the constructor initialization in order to
    # avoid these errors.

    def test_get_value(self) -> None:
        board = [[0, 1, 0], [0, 0, 0], [0, 0, 2]]
        position = (0, 1)
        response = 1
        self._test_get_value(board, position, response)

    def _test_get_value(
        self, board: List[List[int]], position: Tuple[int, int], expected_response: int
    ) -> None:
        model, message_handler = self._get_game_handlers()
        tictactoeboard = model(board)
        response = tictactoeboard.get_value(board, position)
        self.assertEqual(response, expected_response)

    def test_determine_game_over_with_win(self) -> None:
        board = [[1, 1, 1], [0, 2, 0], [2, 0, 2]]
        players = ["Human", "Computer"]
        response = "current turn"
        self._test_determine_game_over_with_win(board, players, response)

    def _test_determine_game_over_with_win(
        self, board: List[List[int]], players: List[str], expected_response: str
    ) -> None:
        model, message_handler = self._get_game_handlers()
        tictactoegame = model(board)
        response = tictactoegame.determine_game_over(players)
        self.assertEqual(response, expected_response)

    def test_determine_game_over_with_draw(self) -> None:
        board = [[1, 2, 1], [1, 2, 1], [2, 1, 2]]
        players = ["Human", "Computer"]
        response = "draw"
        self._test_determine_game_over_with_draw(board, players, response)

    def _test_determine_game_over_with_draw(
        self, board: List[List[int]], players: List[str], expected_response: str
    ) -> None:
        model, message_handler = self._get_game_handlers()
        tictactoeboard = model(board)
        response = tictactoeboard.determine_game_over(players)
        self.assertEqual(response, expected_response)

    def test_board_is_full(self) -> None:
        board = [[1, 0, 1], [1, 2, 1], [2, 1, 2]]
        response = False
        self._test_board_is_full(board, response)

    def _test_board_is_full(self, board: List[List[int]], expected_response: bool) -> None:
        model, message_handler = self._get_game_handlers()
        tictactoeboard = model(board)
        response = tictactoeboard.board_is_full(board)
        self.assertEqual(response, expected_response)

    def test_contains_winning_move(self) -> None:
        board = [[1, 1, 1], [0, 2, 0], [2, 0, 2]]
        response = True
        self._test_contains_winning_move(board, response)

    def _test_contains_winning_move(self, board: List[List[int]], expected_response: bool) -> None:
        model, message_handler = self._get_game_handlers()
        tictactoeboard = model(board)
        response = tictactoeboard.contains_winning_move(board)
        self.assertEqual(response, expected_response)

    def test_get_locations_of_char(self) -> None:
        board = [[0, 0, 0], [0, 0, 0], [0, 0, 1]]
        response = [[2, 2]]
        self._test_get_locations_of_char(board, response)

    def _test_get_locations_of_char(
        self, board: List[List[int]], expected_response: List[List[int]]
    ) -> None:
        model, message_handler = self._get_game_handlers()
        tictactoeboard = model(board)
        response = tictactoeboard.get_locations_of_char(board, 1)
        self.assertEqual(response, expected_response)

    def test_is_valid_move(self) -> None:
        board = [[0, 0, 0], [0, 0, 0], [1, 0, 2]]
        move = "1,2"
        response = True
        self._test_is_valid_move(board, move, response)

        move = "4,4"
        response = False
        self._test_is_valid_move(board, move, response)

    def _test_is_valid_move(
        self, board: List[List[int]], move: str, expected_response: bool
    ) -> None:
        model, message_handler = self._get_game_handlers()
        tictactoeboard = model(board)
        response = tictactoeboard.is_valid_move(move)
        self.assertEqual(response, expected_response)

    def test_player_color(self) -> None:
        turn = 0
        response = ":x:"
        self._test_player_color(turn, response)

    def _test_player_color(self, turn: int, expected_response: str) -> None:
        model, message_handler = self._get_game_handlers()
        response = message_handler.get_player_color(0)

        self.assertEqual(response, expected_response)

    def test_static_responses(self) -> None:
        model, message_handler = self._get_game_handlers()
        self.assertNotEqual(message_handler.get_player_color(0), None)
        self.assertNotEqual(message_handler.game_start_message(), None)
        self.assertEqual(
            message_handler.alert_move_message("foo", "move 3"), "foo put a token at 3"
        )

    def test_has_attributes(self) -> None:
        model, message_handler = self._get_game_handlers()
        self.assertTrue(hasattr(message_handler, "parse_board") is not None)
        self.assertTrue(hasattr(message_handler, "alert_move_message") is not None)
        self.assertTrue(hasattr(model, "current_board") is not None)
        self.assertTrue(hasattr(model, "determine_game_over") is not None)

    def test_parse_board(self) -> None:
        board = [[0, 1, 0], [0, 0, 0], [0, 0, 2]]
        response = ":one: :x: :three:\n\n" + ":four: :five: :six:\n\n" + ":seven: :eight: :o:\n\n"
        self._test_parse_board(board, response)

    def _test_parse_board(self, board: List[List[int]], expected_response: str) -> None:
        model, message_handler = self._get_game_handlers()
        response = message_handler.parse_board(board)
        self.assertEqual(response, expected_response)

    def add_user_to_cache(self, name: str, bot: Any = None) -> Any:
        if bot is None:
            bot, bot_handler = self._get_handlers()
        message = {
            "sender_email": f"{name}@example.com",
            "sender_full_name": f"{name}",
        }
        bot.add_user_to_cache(message)
        return bot

    def setup_game(self) -> None:
        bot = self.add_user_to_cache("foo")
        self.add_user_to_cache("baz", bot)
        instance = GameInstance(
            bot, False, "test game", "abc123", ["foo@example.com", "baz@example.com"], "test"
        )
        bot.instances.update({"abc123": instance})
        instance.start()
        return bot

    def _get_game_handlers(self) -> Tuple[Any, Any]:
        bot, bot_handler = self._get_handlers()
        return bot.model, bot.game_message_handler

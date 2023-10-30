from typing import Any, List, Tuple

from zulip_bots.game_handler import GameInstance
from zulip_bots.test_lib import BotTestCase, DefaultTests

from .libraries.constants import EMPTY_BOARD


class TestMerelsBot(BotTestCase, DefaultTests):
    bot_name = "merels"

    def test_no_command(self):
        message = dict(
            content="magic", type="stream", sender_email="boo@email.com", sender_full_name="boo"
        )
        res = self.get_response(message)
        self.assertEqual(
            res["content"], "You are not in a game at the moment. Type `help` for help."
        )

    # FIXME: Add tests for computer moves
    # FIXME: Add test lib for game_handler

    # Test for unchanging aspects within the game
    # Player Color, Start Message, Moving Message
    def test_static_responses(self) -> None:
        model, message_handler = self._get_game_handlers()
        self.assertNotEqual(message_handler.get_player_color(0), None)
        self.assertNotEqual(message_handler.game_start_message(), None)
        self.assertEqual(
            message_handler.alert_move_message("foo", "moved right"), "foo :moved right"
        )

    # Test to see if the attributes exist
    def test_has_attributes(self) -> None:
        model, message_handler = self._get_game_handlers()
        # Attributes from the Merels Handler
        self.assertTrue(hasattr(message_handler, "parse_board") is not None)
        self.assertTrue(hasattr(message_handler, "get_player_color") is not None)
        self.assertTrue(hasattr(message_handler, "alert_move_message") is not None)
        self.assertTrue(hasattr(message_handler, "game_start_message") is not None)
        self.assertTrue(hasattr(message_handler, "alert_move_message") is not None)
        # Attributes from the Merels Model
        self.assertTrue(hasattr(model, "determine_game_over") is not None)
        self.assertTrue(hasattr(model, "contains_winning_move") is not None)
        self.assertTrue(hasattr(model, "make_move") is not None)

    def test_parse_board(self) -> None:
        board = EMPTY_BOARD
        expect_response = EMPTY_BOARD
        self._test_parse_board(board, expect_response)

    def test_add_user_to_cache(self):
        self.add_user_to_cache("Name")

    def test_setup_game(self):
        self.setup_game()

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

    def _test_parse_board(self, board: str, expected_response: str) -> None:
        model, message_handler = self._get_game_handlers()
        response = message_handler.parse_board(board)
        self.assertEqual(response, expected_response)

    def _test_determine_game_over(
        self, board: List[List[int]], players: List[str], expected_response: str
    ) -> None:
        model, message_handler = self._get_game_handlers()
        response = model.determine_game_over(players)
        self.assertEqual(response, expected_response)

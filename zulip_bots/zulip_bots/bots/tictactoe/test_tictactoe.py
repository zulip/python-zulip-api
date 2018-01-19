from zulip_bots.test_lib import BotTestCase
from zulip_bots.game_handler import GameInstance

from unittest.mock import patch
from typing import List, Tuple, Any


class TestTicTacToeBot(BotTestCase):
    bot_name = 'tictactoe'

    # FIXME: Add tests for computer moves
    # FIXME: Add test lib for game_handler

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

    def _test_determine_game_over(self, board: List[List[int]], players: List[str], expected_response: str) -> None:
        model, message_handler = self._get_game_handlers()
        response = model.determine_game_over(players)
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

from typing import Any, List

from zulip_bots.game_handler import BadMoveError, GameAdapter


class GameHandlerBotMessageHandler:
    tokens = (":blue_circle:", ":red_circle:")

    def parse_board(self, board: Any) -> str:
        return "foo"

    def get_player_color(self, turn: int) -> str:
        return self.tokens[turn]

    def alert_move_message(self, original_player: str, move_info: str) -> str:
        column_number = move_info.replace("move ", "")
        return original_player + " moved in column " + column_number

    def game_start_message(self) -> str:
        return "Type `move <column>` to place a token.\n \
The first player to get 4 in a row wins!\n \
Good Luck!"


class MockModel:
    def __init__(self) -> None:
        self.current_board = "mock board"

    def make_move(self, move: str, player: int, is_computer: bool = False) -> Any:
        if not is_computer:
            if int(move.replace("move ", "")) < 9:
                return "mock board"
            else:
                raise BadMoveError("Invalid Move.")
        return "mock board"

    def determine_game_over(self, players: List[str]) -> None:
        return None


class GameHandlerBotHandler(GameAdapter):
    """
    DO NOT USE THIS BOT
    This bot is used to test game_handler.py
    """

    def __init__(self) -> None:
        game_name = "foo test game"
        bot_name = "game_handler_bot"
        move_help_message = "* To make your move during a game, type\n```move <column-number>```"
        move_regex = r"move (\d)$"
        model = MockModel
        game_message_handler = GameHandlerBotMessageHandler
        rules = ""

        super().__init__(
            game_name,
            bot_name,
            move_help_message,
            move_regex,
            model,
            game_message_handler,
            rules,
            max_players=2,
            supports_computer=True,
        )


handler_class = GameHandlerBotHandler

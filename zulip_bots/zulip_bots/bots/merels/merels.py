from typing import Any, Final, List

from typing_extensions import override

from zulip_bots.game_handler import GameAdapter, SamePlayerMoveError

from .libraries import database, game, game_data, mechanics


class Storage:
    def __init__(self, topic_name):
        self.data = {}
        self.data[topic_name] = '["X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0]'

    def put(self, topic_name, value: str):
        self.data[topic_name] = value

    def get(self, topic_name):
        return self.data[topic_name]


class MerelsModel:
    def __init__(self, board: Any = None) -> None:
        self.topic = "merels"
        self.storage = Storage(self.topic)
        self.current_board = mechanics.display_game(self.topic, self.storage)
        self.token = ["O", "X"]

    def determine_game_over(self, players: List[str]) -> str:
        if self.contains_winning_move(self.current_board):
            return "current turn"
        return ""

    def contains_winning_move(self, board: Any) -> bool:
        merels = database.MerelsStorage(self.topic, self.storage)
        data = game_data.GameData(merels.get_game_data(self.topic))

        return data.get_phase() > 1 and (
            mechanics.get_piece("X", data.grid()) <= 2 or mechanics.get_piece("O", data.grid()) <= 2
        )

    def make_move(self, move: str, player_number: int, computer_move: bool = False) -> Any:
        if self.storage.get(self.topic) == '["X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0]':
            self.storage.put(
                self.topic,
                f'["{self.token[player_number]}", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0]',
            )
        self.current_board, same_player_move = game.beat(move, self.topic, self.storage)
        if same_player_move != "":
            raise SamePlayerMoveError(same_player_move)
        return self.current_board


class MerelsMessageHandler:
    tokens = (":o_button:", ":cross_mark_button:")

    def parse_board(self, board: Any) -> str:
        return board

    def get_player_color(self, turn: int) -> str:
        return self.tokens[turn]

    def alert_move_message(self, original_player: str, move_info: str) -> str:
        return original_player + " :" + move_info

    def game_start_message(self) -> str:
        return game.get_help()


class MerelsHandler(GameAdapter):
    """
    You can play merels! Make sure your message starts with
    "@mention-bot".
    """

    META: Final = {
        "name": "merels",
        "description": "Lets you play merels against any player.",
    }

    @override
    def usage(self) -> str:
        return game.get_info()

    def __init__(self) -> None:
        game_name = "Merels"
        bot_name = "merels"
        move_help_message = ""
        move_regex = ".*"
        model = MerelsModel
        rules = game.get_info()
        game_message_handler = MerelsMessageHandler
        super().__init__(
            game_name,
            bot_name,
            move_help_message,
            move_regex,
            model,
            game_message_handler,
            rules,
            max_players=2,
            min_players=2,
            supports_computer=False,
        )


handler_class = MerelsHandler

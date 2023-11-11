import copy
from typing import Any, Dict, Final, List, Tuple

from zulip_bots.game_handler import BadMoveError, GameAdapter


class GameOfFifteenModel:
    final_board: Final = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]

    initial_board: Final = [[8, 7, 6], [5, 4, 3], [2, 1, 0]]

    def __init__(self, board: Any = None) -> None:
        if board is not None:
            self.current_board = board
        else:
            self.current_board = copy.deepcopy(self.initial_board)

    def get_coordinates(self, board: List[List[int]]) -> Dict[int, Tuple[int, int]]:
        return {
            board[0][0]: (0, 0),
            board[0][1]: (0, 1),
            board[0][2]: (0, 2),
            board[1][0]: (1, 0),
            board[1][1]: (1, 1),
            board[1][2]: (1, 2),
            board[2][0]: (2, 0),
            board[2][1]: (2, 1),
            board[2][2]: (2, 2),
        }

    def determine_game_over(self, players: List[str]) -> str:
        if self.won(self.current_board):
            return "current turn"
        return ""

    def won(self, board: Any) -> bool:
        for i in range(3):
            for j in range(3):
                if board[i][j] != self.final_board[i][j]:
                    return False
        return True

    def validate_move(self, tile: int) -> bool:
        if tile < 1 or tile > 8:
            return False
        return True

    def update_board(self, board):
        self.current_board = copy.deepcopy(board)

    def make_move(self, move: str, player_number: int, computer_move: bool = False) -> Any:
        board = self.current_board
        move = move.strip()
        move = move.split(" ")

        if "" in move:
            raise BadMoveError("You should enter space separated digits.")
        moves = len(move)
        for m in range(1, moves):
            tile = int(move[m])
            coordinates = self.get_coordinates(board)
            if tile not in coordinates:
                raise BadMoveError("You can only move tiles which exist in the board.")
            i, j = coordinates[tile]
            if j - 1 > -1 and board[i][j - 1] == 0:
                board[i][j - 1] = tile
                board[i][j] = 0
            elif i - 1 > -1 and board[i - 1][j] == 0:
                board[i - 1][j] = tile
                board[i][j] = 0
            elif j + 1 < 3 and board[i][j + 1] == 0:
                board[i][j + 1] = tile
                board[i][j] = 0
            elif i + 1 < 3 and board[i + 1][j] == 0:
                board[i + 1][j] = tile
                board[i][j] = 0
            else:
                raise BadMoveError("You can only move tiles which are adjacent to :grey_question:.")
            if m == moves - 1:
                return board


class GameOfFifteenMessageHandler:
    tiles: Final = {
        "0": ":grey_question:",
        "1": ":one:",
        "2": ":two:",
        "3": ":three:",
        "4": ":four:",
        "5": ":five:",
        "6": ":six:",
        "7": ":seven:",
        "8": ":eight:",
    }

    def parse_board(self, board: Any) -> str:
        # Header for the top of the board
        board_str = ""

        for row in range(3):
            board_str += "\n\n"
            for column in range(3):
                board_str += self.tiles[str(board[row][column])]
        return board_str

    def alert_move_message(self, original_player: str, move_info: str) -> str:
        tile = move_info.replace("move ", "")
        return original_player + " moved " + tile

    def game_start_message(self) -> str:
        return (
            "Welcome to Game of Fifteen!"
            "To make a move, type @-mention `move <tile1> <tile2> ...`"
        )


class GameOfFifteenBotHandler(GameAdapter):
    """
    Bot that uses the Game Adapter class
    to allow users to play Game of Fifteen
    """

    def __init__(self) -> None:
        game_name = "Game of Fifteen"
        bot_name = "Game of Fifteen"
        move_help_message = (
            "* To make your move during a game, type\n```move <tile1> <tile2> ...```"
        )
        move_regex = r"move [\d{1}\s]+$"
        model = GameOfFifteenModel
        game_message_handler = GameOfFifteenMessageHandler
        rules = """Arrange the board’s tiles from smallest to largest, left to right,
                  top to bottom, and tiles adjacent to :grey_question: can only be moved.
                  Final configuration will have :grey_question: in top left."""

        super().__init__(
            game_name,
            bot_name,
            move_help_message,
            move_regex,
            model,
            game_message_handler,
            rules,
            min_players=1,
            max_players=1,
        )


handler_class = GameOfFifteenBotHandler

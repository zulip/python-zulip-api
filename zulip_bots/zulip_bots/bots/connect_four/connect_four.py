from zulip_bots.game_handler import GameAdapter
from zulip_bots.bots.connect_four.controller import ConnectFourModel
from typing import Any


class ConnectFourMessageHandler(object):
    tokens = [':blue_circle:', ':red_circle:']

    def parse_board(self, board: Any) -> str:
        # Header for the top of the board
        board_str = ':one: :two: :three: :four: :five: :six: :seven:'

        for row in range(0, 6):
            board_str += '\n\n'
            for column in range(0, 7):
                if board[row][column] == 0:
                    board_str += ':heavy_large_circle: '
                elif board[row][column] == 1:
                    board_str += ':blue_circle: '
                elif board[row][column] == -1:
                    board_str += ':red_circle: '

        return board_str

    def get_player_color(self, turn: int) -> str:
        return self.tokens[turn]

    def alert_move_message(self, original_player: str, move_info: str) -> str:
        column_number = move_info.replace('move ', '')
        return original_player + ' moved in column ' + column_number

    def game_start_message(self) -> str:
        return 'Type `move <column-number>` or `<column-number>` to place a token.\n\
The first player to get 4 in a row wins!\n Good Luck!'


class ConnectFourBotHandler(GameAdapter):
    '''
    Bot that uses the Game Adapter class
    to allow users to play other users
    or the comptuer in a game of Connect
    Four
    '''

    def __init__(self) -> None:
        game_name = 'Connect Four'
        bot_name = 'connect_four'
        move_help_message = '* To make your move during a game, type\n' \
                            '```move <column-number>``` or ```<column-number>```'
        move_regex = '(move ([1-7])$)|(([1-7])$)'
        model = ConnectFourModel
        gameMessageHandler = ConnectFourMessageHandler
        rules = '''Try to get four pieces in row, Diagonals count too!'''

        super(ConnectFourBotHandler, self).__init__(
            game_name,
            bot_name,
            move_help_message,
            move_regex,
            model,
            gameMessageHandler,
            rules,
            max_players=2
        )


handler_class = ConnectFourBotHandler

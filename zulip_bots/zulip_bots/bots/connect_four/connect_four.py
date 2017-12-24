from zulip_bots.bots.connect_four.game_adapter import GameAdapter
from zulip_bots.bots.connect_four.controller import ConnectFourModel

class ConnectFourMessageHandler(object):
    tokens = [':blue_circle:', ':red_circle:']

    def parse_board(self, board):
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

    def get_player_color(self, turn):
        return self.tokens[turn]

    def alert_move_message(self, original_player, move_info):
        column_number = move_info
        return '**' + original_player + ' moved in column ' + str(column_number + 1) + '**.'

    def confirm_move_message(self, move_info):
        column_number = move_info
        return 'You placed your token in column ' + str(column_number + 1) + '.'

    def invalid_move_message(self):
        return 'Please specify a column between 1 and 7 with at least one open spot.'

class ConnectFourBotHandler(GameAdapter):
    '''
    Bot that uses the Game Adapter class
    to allow users to play other users
    or the comptuer in a game of Connect
    Four
    '''

    def __init__(self):
        game_name = 'Connect Four'
        bot_name = 'connect_four'
        move_help_message = '* To make your move during a game, type\n' \
                            '```move <column-number>```'
        move_regex = 'move (\d)$'
        model = ConnectFourModel
        gameMessageHandler = ConnectFourMessageHandler

        super(ConnectFourBotHandler, self).__init__(game_name, bot_name, move_help_message, move_regex, model, gameMessageHandler)

handler_class = ConnectFourBotHandler

from copy import deepcopy
from random import randint
from functools import reduce
from zulip_bots.game_handler import BadMoveException


class ConnectFourModel(object):
    '''
    Object that manages running the Connect
    Four logic for the Connect Four Bot
    '''

    def __init__(self):
        self.blank_board = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0]
        ]

        self.current_board = self.blank_board

    def update_board(self, board):
        self.current_board = deepcopy(board)

    def get_column(self, col):
        # We use this in tests.
        return [
            self.current_board[i][col]
            for i in range(6)
        ]

    def validate_move(self, column_number):
        if column_number < 0 or column_number > 6:
            return False

        row = 0
        column = column_number

        return self.current_board[row][column] == 0

    def available_moves(self):
        available_moves = []
        row = 0
        for column in range(0, 7):
            if self.current_board[row][column] == 0:
                available_moves.append(column)

        return available_moves

    def make_move(self, move, player_number, is_computer=False):
        if player_number == 1:
            token_number = -1
        if player_number == 0:
            token_number = 1
        finding_move = True
        row = 5
        column = int(move.replace('move ', '')) - 1

        while finding_move:
            if row < 0:
                raise BadMoveException('Make sure your move is in a column with free space.')
            if self.current_board[row][column] == 0:
                self.current_board[row][column] = token_number
                finding_move = False

            row -= 1

        return deepcopy(self.current_board)

    def determine_game_over(self, players):
        def get_horizontal_wins(board):
            horizontal_sum = 0

            for row in range(0, 6):
                for column in range(0, 4):
                    horizontal_sum = board[row][column] + board[row][column + 1] + \
                        board[row][column + 2] + board[row][column + 3]
                    if horizontal_sum == -4:
                        return -1
                    elif horizontal_sum == 4:
                        return 1

            return 0

        def get_vertical_wins(board):
            vertical_sum = 0

            for row in range(0, 3):
                for column in range(0, 7):
                    vertical_sum = board[row][column] + board[row + 1][column] + \
                        board[row + 2][column] + board[row + 3][column]
                    if vertical_sum == -4:
                        return -1
                    elif vertical_sum == 4:
                        return 1

            return 0

        def get_diagonal_wins(board):
            major_diagonal_sum = 0
            minor_diagonal_sum = 0

            # Major Diagonl Sum
            for row in range(0, 3):
                for column in range(0, 4):
                    major_diagonal_sum = board[row][column] + board[row + 1][column + 1] + \
                        board[row + 2][column + 2] + board[row + 3][column + 3]
                    if major_diagonal_sum == -4:
                        return -1
                    elif major_diagonal_sum == 4:
                        return 1

            # Minor Diagonal Sum
            for row in range(3, 6):
                for column in range(0, 4):
                    minor_diagonal_sum = board[row][column] + board[row - 1][column + 1] + \
                        board[row - 2][column + 2] + board[row - 3][column + 3]
                    if minor_diagonal_sum == -4:
                        return -1
                    elif minor_diagonal_sum == 4:
                        return 1

            return 0

        first_player, second_player = players[0], players[1]
        # If all tokens in top row are filled (its a draw), product != 0
        top_row_multiple = reduce(lambda x, y: x * y, self.current_board[0])

        if top_row_multiple != 0:
            return 'draw'

        winner = get_horizontal_wins(self.current_board) + \
            get_vertical_wins(self.current_board) + \
            get_diagonal_wins(self.current_board)

        if winner == 1:
            return first_player
        elif winner == -1:
            return second_player

        return ''

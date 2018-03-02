import copy
import random

from typing import List, Any, Tuple
from zulip_bots.game_handler import GameAdapter, BadMoveException

# -------------------------------------

State = List[List[str]]


class TicTacToeModel(object):
    smarter = True
    # If smarter is True, the computer will do some extra thinking - it'll be harder for the user.

    triplets = [[(0, 0), (0, 1), (0, 2)],  # Row 1
                [(1, 0), (1, 1), (1, 2)],  # Row 2
                [(2, 0), (2, 1), (2, 2)],  # Row 3
                [(0, 0), (1, 0), (2, 0)],  # Column 1
                [(0, 1), (1, 1), (2, 1)],  # Column 2
                [(0, 2), (1, 2), (2, 2)],  # Column 3
                [(0, 0), (1, 1), (2, 2)],  # Diagonal 1
                [(0, 2), (1, 1), (2, 0)]   # Diagonal 2
                ]

    initial_board = [[0, 0, 0],
                     [0, 0, 0],
                     [0, 0, 0]]

    def __init__(self, board: Any=None) -> None:
        if board is not None:
            self.current_board = board
        else:
            self.current_board = copy.deepcopy(self.initial_board)

    def get_value(self, board: Any, position: Tuple[int, int]) -> int:
        return board[position[0]][position[1]]

    def determine_game_over(self, players: List[str]) -> str:
        if self.contains_winning_move(self.current_board):
            return 'current turn'
        if self.board_is_full(self.current_board):
            return 'draw'
        return ''

    def board_is_full(self, board: Any) -> bool:
        ''' Determines if the board is full or not. '''
        for row in board:
            for element in row:
                if element == 0:
                    return False
        return True

    # Used for current board & trial computer board
    def contains_winning_move(self, board: Any) -> bool:
        ''' Returns true if all coordinates in a triplet have the same value in them (x or o) and no coordinates
        in the triplet are blank. '''
        for triplet in self.triplets:
            if (self.get_value(board, triplet[0]) == self.get_value(board, triplet[1]) ==
                    self.get_value(board, triplet[2]) != 0):
                return True
        return False

    def get_locations_of_char(self, board: Any, char: int) -> List[List[int]]:
        ''' Gets the locations of the board that have char in them. '''
        locations = []
        for row in range(3):
            for col in range(3):
                if board[row][col] == char:
                    locations.append([row, col])
        return locations

    def two_blanks(self, triplet: List[Tuple[int, int]], board: Any) -> List[Tuple[int, int]]:
        ''' Determines which rows/columns/diagonals have two blank spaces and an 2 already in them. It's more advantageous
        for the computer to move there. This is used when the computer makes its move. '''

        o_found = False
        for position in triplet:
            if self.get_value(board, position) == 2:
                o_found = True
                break

        blanks_list = []
        if o_found:
            for position in triplet:
                if self.get_value(board, position) == 0:
                    blanks_list.append(position)

            if len(blanks_list) == 2:
                return blanks_list
        return []

    def computer_move(self, board: Any, player_number: Any) -> Any:
        ''' The computer's logic for making its move. '''
        my_board = copy.deepcopy(
            board)  # First the board is copied; used later on
        blank_locations = self.get_locations_of_char(my_board, 0)
        # Gets the locations that already have x's
        x_locations = self.get_locations_of_char(board, 1)
        # List of the coordinates of the corners of the board
        corner_locations = [[0, 0], [0, 2], [2, 0], [2, 2]]
        # List of the coordinates of the edge spaces of the board
        edge_locations = [[1, 0], [0, 1], [1, 2], [2, 1]]

        # If no empty spaces are left, the computer can't move anyway, so it just returns the board.
        if blank_locations == []:
            return board

        # This is special logic only used on the first move.
        if len(x_locations) == 1:
            # If the user played first in the corner or edge,
            # the computer should move in the center.
            if x_locations[0] in corner_locations or x_locations[0] in edge_locations:
                board[1][1] = 2
            # If user played first in the center, the computer should move in the corner. It doesn't matter which corner.
            else:
                location = random.choice(corner_locations)
                row = location[0]
                col = location[1]
                board[row][col] = 2
            return board

        # This logic is used on all other moves.
        # First I'll check if the computer can win in the next move. If so, that's where the computer will play.
        # The check is done by replacing the blank locations with o's and seeing if the computer would win in each case.
        for row, col in blank_locations:
            my_board[row][col] = 2
            if self.contains_winning_move(my_board):
                board[row][col] = 2
                return board
            else:
                my_board[row][col] = 0  # Revert if not winning

        # If the computer can't immediately win, it wants to make sure the user can't win in their next move, so it
        # checks to see if the user needs to be blocked.
        # The check is done by replacing the blank locations with x's and seeing if the user would win in each case.
        for row, col in blank_locations:
            my_board[row][col] = 1
            if self.contains_winning_move(my_board):
                board[row][col] = 2
                return board
            else:
                my_board[row][col] = 0  # Revert if not winning

        # Assuming nobody will win in their next move, now I'll find the best place for the computer to win.
        for row, col in blank_locations:
            if (1 not in my_board[row] and my_board[0][col] != 1 and my_board[1][col] !=
                    1 and my_board[2][col] != 1):
                board[row][col] = 2
                return board

        # If no move has been made, choose a random blank location. If smarter is True, the computer will choose a
        # random blank location from a set of better locations to play. These locations are determined by seeing if
        # there are two blanks and an 2 in each row, column, and diagonal (done in two_blanks).
        # If smarter is False, all blank locations can be chosen.
        if self.smarter:
            blanks = []  # type: Any
            for triplet in self.triplets:
                result = self.two_blanks(triplet, board)
                if result:
                    blanks = blanks + result
            blank_set = set(blanks)
            blank_list = list(blank_set)
            if blank_list == []:
                location = random.choice(blank_locations)
            else:
                location = random.choice(blank_list)
            row = location[0]
            col = location[1]
            board[row][col] = 2
            return board

        else:
            location = random.choice(blank_locations)
            row = location[0]
            col = location[1]
            board[row][col] = 2
            return board

    def is_valid_move(self, move: str) -> bool:
        ''' Checks the validity of the coordinate input passed in to make sure it's not out-of-bounds (ex. 5, 5) '''
        try:
            split_move = move.split(",")
            row = split_move[0].strip()
            col = split_move[1].strip()
            valid = False
            if row in ("1", "2", "3") and col in ("1", "2", "3"):
                valid = True
        except IndexError:
            valid = False
        return valid

    def make_move(self, move: str, player_number: int, computer_move: bool=False) -> Any:
        if computer_move:
            return self.computer_move(self.current_board, player_number + 1)
        move_coords_str = coords_from_command(move)
        if not self.is_valid_move(move_coords_str):
            raise BadMoveException('Make sure your move is from 0-9')
        board = self.current_board
        move_coords = move_coords_str.split(',')
        # Subtraction must be done to convert to the right indices,
        # since computers start numbering at 0.
        row = (int(move_coords[1])) - 1
        column = (int(move_coords[0])) - 1
        if board[row][column] != 0:
            raise BadMoveException('Make sure your space hasn\'t already been filled.')
        board[row][column] = player_number + 1
        return board


class TicTacToeMessageHandler(object):
    tokens = [':cross_mark_button:', ':o_button:']

    def parse_row(self, row: Tuple[int, int], row_num: int) -> str:
        ''' Takes the row passed in as a list and returns it as a string. '''
        row_chars = []
        num_symbols = [':one:', ':two:', ':three:', ':four:', ':five:', ':six:', ':seven:', ':eight:', ':nine:']
        for i, e in enumerate(row):
            if e == 0:
                row_chars.append(num_symbols[row_num * 3 + i])
            else:
                row_chars.append(self.get_player_color(e - 1))
        row_string = ' '.join(row_chars)
        return row_string + '\n\n'

    def parse_board(self, board: Any) -> str:
        ''' Takes the board as a nested list and returns a nice version for the user. '''
        return "".join([self.parse_row(r, r_num) for r_num, r in enumerate(board)])

    def get_player_color(self, turn: int) -> str:
        return self.tokens[turn]

    def alert_move_message(self, original_player: str, move_info: str) -> str:
        move_info = move_info.replace('move ', '')
        return '{} put a token at {}'.format(original_player, move_info)

    def game_start_message(self) -> str:
        return ("Welcome to tic-tac-toe!"
                "To make a move, type @-mention `move <number>` or `<number>`")


class ticTacToeHandler(GameAdapter):
    '''
    You can play tic-tac-toe! Make sure your message starts with
    "@mention-bot".
    '''
    META = {
        'name': 'TicTacToe',
        'description': 'Lets you play Tic-tac-toe against a computer.',
    }

    def usage(self) -> str:
        return '''
            You can play tic-tac-toe now! Make sure your
            message starts with @mention-bot.
            '''

    def __init__(self) -> None:
        game_name = 'Tic Tac Toe'
        bot_name = 'tictactoe'
        move_help_message = '* To move during a game, type\n`move <number>` or `<number>`'
        move_regex = '(move (\d)$)|((\d)$)'
        model = TicTacToeModel
        gameMessageHandler = TicTacToeMessageHandler
        rules = '''Try to get three in horizontal or vertical or diagonal row to win the game.'''
        super(ticTacToeHandler, self).__init__(
            game_name,
            bot_name,
            move_help_message,
            move_regex,
            model,
            gameMessageHandler,
            rules,
            supports_computer=True
        )


def coords_from_command(cmd: str) -> str:
    # This function translates the input command into a TicTacToeGame move.
    # It should return two indices, each one of (1,2,3), separated by a comma, eg. "3,2"
    ''' As there are various ways to input a coordinate (with/without parentheses, with/without spaces, etc.) the
    input is stripped to just the numbers before being used in the program. '''
    cmd_num = int(cmd.replace('move ', '')) - 1
    cmd = '{},{}'.format((cmd_num % 3) + 1, (cmd_num // 3) + 1)
    return cmd


handler_class = ticTacToeHandler

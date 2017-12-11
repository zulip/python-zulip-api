import copy
import random

from typing import List

# -------------------------------------

State = List[List[str]]

class TicTacToeGame(object):
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

    initial_board = [["_", "_", "_"],
                     ["_", "_", "_"],
                     ["_", "_", "_"]]

    def __init__(self, board=None):
        if board is not None:
            self.board = board
        else:
            self.board = copy.deepcopy(self.initial_board)

    def get_state(self) -> State:
        return self.board

    def is_new_game(self) -> bool:
        return self.board == self.initial_board

    def display_row(self, row):
        ''' Takes the row passed in as a list and returns it as a string. '''
        row_string = " ".join([e.strip() for e in row])
        return("[ {} ]\n".format(row_string))

    def display_board(self, board):
        ''' Takes the board as a nested list and returns a nice version for the user. '''
        return "".join([self.display_row(r) for r in board])

    def get_value(self, board, position):
        return board[position[0]][position[1]]

    def board_is_full(self, board):
        ''' Determines if the board is full or not. '''
        full = False
        board_state = ""
        for row in board:
            for element in row:
                if element == "_":
                    board_state += "_"
        if "_" not in board_state:
            full = True
        return full

    def win_conditions(self, board, triplets):
        ''' Returns true if all coordinates in a triplet have the same value in them (x or o) and no coordinates
        in the triplet are blank. '''
        won = False
        for triplet in triplets:
            if (self.get_value(board, triplet[0]) == self.get_value(board, triplet[1]) ==
                    self.get_value(board, triplet[2]) != "_"):
                won = True
                break
        return won

    def get_locations_of_char(self, board, char):
        ''' Gets the locations of the board that have char in them. '''
        locations = []
        for row in range(3):
            for col in range(3):
                if board[row][col] == char:
                    locations.append([row, col])
        return locations

    def two_blanks(self, triplet, board):
        ''' Determines which rows/columns/diagonals have two blank spaces and an 'o' already in them. It's more advantageous
        for the computer to move there. This is used when the computer makes its move. '''

        o_found = False
        for position in triplet:
            if self.get_value(board, position) == "o":
                o_found = True
                break

        blanks_list = []
        if o_found:
            for position in triplet:
                if self.get_value(board, position) == "_":
                    blanks_list.append(position)

            if len(blanks_list) == 2:
                return blanks_list

    def computer_move(self, board):
        ''' The computer's logic for making its move. '''
        my_board = copy.deepcopy(board)  # First the board is copied; used later on
        blank_locations = self.get_locations_of_char(my_board, "_")
        x_locations = self.get_locations_of_char(board, "x")  # Gets the locations that already have x's
        corner_locations = [[0, 0], [0, 2], [2, 0], [2, 2]]  # List of the coordinates of the corners of the board
        edge_locations = [[1, 0], [0, 1], [1, 2], [2, 1]]  # List of the coordinates of the edge spaces of the board

        if blank_locations == []:  # If no empty spaces are left, the computer can't move anyway, so it just returns the board.
            return board

        if len(x_locations) == 1:  # This is special logic only used on the first move.
            # If the user played first in the corner or edge, the computer should move in the center.
            if x_locations[0] in corner_locations or x_locations[0] in edge_locations:
                board[1][1] = "o"
            # If user played first in the center, the computer should move in the corner. It doesn't matter which corner.
            else:
                location = random.choice(corner_locations)
                row = location[0]
                col = location[1]
                board[row][col] = "o"
            return board

        # This logic is used on all other moves.
        # First I'll check if the computer can win in the next move. If so, that's where the computer will play.
        # The check is done by replacing the blank locations with o's and seeing if the computer would win in each case.
        for row, col in blank_locations:
            my_board[row][col] = "o"
            if self.win_conditions(my_board, self.triplets):
                board[row][col] = "o"
                return board
            else:
                my_board[row][col] = "_"  # Revert if not winning

        # If the computer can't immediately win, it wants to make sure the user can't win in their next move, so it
        # checks to see if the user needs to be blocked.
        # The check is done by replacing the blank locations with x's and seeing if the user would win in each case.
        for row, col in blank_locations:
            my_board[row][col] = "x"
            if self.win_conditions(my_board, self.triplets):
                board[row][col] = "o"
                return board
            else:
                my_board[row][col] = "_"  # Revert if not winning

        # Assuming nobody will win in their next move, now I'll find the best place for the computer to win.
        for row, col in blank_locations:
            if ('x' not in my_board[row] and my_board[0][col] != 'x' and my_board[1][col] !=
                    'x' and my_board[2][col] != 'x'):
                board[row][col] = 'o'
                return board

        # If no move has been made, choose a random blank location. If smarter is True, the computer will choose a
        # random blank location from a set of better locations to play. These locations are determined by seeing if
        # there are two blanks and an 'o' in each row, column, and diagonal (done in two_blanks).
        # If smarter is False, all blank locations can be chosen.
        if self.smarter:
            blanks = []
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
            board[row][col] = 'o'
            return board

        else:
            location = random.choice(blank_locations)
            row = location[0]
            col = location[1]
            board[row][col] = 'o'
            return board

    def check_validity(self, move):
        ''' Checks the validity of the coordinate input passed in to make sure it's not out-of-bounds (ex. 5, 5) '''
        try:
            split_move = move.split(",")
            row = split_move[0].strip()
            col = split_move[1].strip()
            valid = False
            if row == "1" or row == "2" or row == "3":
                if col == "1" or col == "2" or col == "3":
                    valid = True
        except IndexError:
            valid = False
        return valid

    def sanitize_move(self, move):
        ''' As there are various ways to input a coordinate (with/without parentheses, with/without spaces, etc.) the
        input is stripped to just the numbers before being used in the program. '''
        move = move.replace("(", "")
        move = move.replace(")", "")
        move = move.strip()
        return move

    def tictactoe(self, input_string):
        board = self.board
        printed_boards = dict(after_player = "", after_computer = "")
        move = self.sanitize_move(input_string)

        # Subtraction must be done to convert to the right indices, since computers start numbering at 0.
        row = (int(move[0])) - 1
        column = (int(move[-1])) - 1

        if board[row][column] != "_":
            return ("filled", printed_boards)
        else:
            board[row][column] = "x"

        printed_boards['after_player'] = self.display_board(board)

        # Check to see if the user won/drew after they made their move. If not, it's the computer's turn.
        if self.win_conditions(board, self.triplets):
            return ("player_win", printed_boards)

        if self.board_is_full(board):
            return ("draw", printed_boards)

        self.computer_move(board)
        printed_boards['after_computer'] = self.display_board(board)

        # Checks to see if the computer won after it makes its move. (The computer can't draw, so there's no point
        # in checking.) If the computer didn't win, the user gets another turn.
        if self.win_conditions(board, self.triplets):
            return ("computer_win", printed_boards)

        return ("next_turn", printed_boards)

# -------------------------------------
long_help_text = ("*Help for Tic-Tac-Toe bot* \n"
                  "The bot responds to messages starting with @mention-bot.\n"
                  "**@mention-bot new** will start a new game (but not if you're "
                  "already in the middle of a game). You must type this first to start playing!\n"
                  "**@mention-bot help** will return this help function.\n"
                  "**@mention-bot quit** will quit from the current game.\n"
                  "**@mention-bot <coordinate>** will make a move at the given coordinate.\n"
                  "Coordinates are entered in a (row, column) format. Numbering is from "
                  "top to bottom and left to right. \n"
                  "Here are the coordinates of each position. (Parentheses and spaces are optional). \n"
                  "(1, 1)  (1, 2)  (1, 3) \n(2, 1)  (2, 2)  (2, 3) \n(3, 1) (3, 2) (3, 3) \n")

short_help_text = "Type **@tictactoe help** or **@ttt help** to see valid inputs."

new_game_text = ("Welcome to tic-tac-toe! You'll be x's and I'll be o's."
                 " Your move first!\n"
                 "Coordinates are entered in a (row, column) format. "
                 "Numbering is from top to bottom and left to right.\n"
                 "Here are the coordinates of each position. (Parentheses and spaces are optional.) \n"
                 "(1, 1)  (1, 2)  (1, 3) \n(2, 1)  (2, 2)  (2, 3) \n(3, 1) (3, 2) (3, 3) \n "
                 "Your move would be one of these. To make a move, type @mention-bot "
                 "followed by a space and the coordinate.")
quit_game_text = "You've successfully quit the game."
unknown_message_text = "Hmm, I didn't understand your input."
already_playing_text = "You're already playing a game!"

mid_move_text = "My turn:"
end_of_move_text = {
    "filled": "That space is already filled, sorry!",
    "next_turn": "Your turn! Enter a coordinate or type help.",
    "computer_win": "Game over! I've won!",
    "player_win": "Game over! You've won!",
    "draw": "It's a draw! Neither of us was able to win.",
}
# -------------------------------------
class ticTacToeHandler(object):
    '''
    You can play tic-tac-toe in a private message with
    tic-tac-toe bot! Make sure your message starts with
    "@mention-bot".
    '''
    META = {
        'name': 'TicTacToe',
        'description': 'Lets you play Tic-tac-toe against a computer.',
    }

    def usage(self):
        return '''
            You can play tic-tac-toe with the computer now! Make sure your
            message starts with @mention-bot.
            '''

    def handle_message(self, message, bot_handler):
        command = message['content']
        original_sender = message['sender_email']

        storage = bot_handler.storage
        if not storage.contains(original_sender):
            storage.put(original_sender, None)
        state = storage.get(original_sender)
        user_game = TicTacToeGame(state) if state else None

        move = None
        if command == 'new':
            if not user_game:
                user_game = TicTacToeGame()
                move = "new"
            if not user_game.is_new_game():
                response = " ".join([already_playing_text, short_help_text])
            else:
                response = new_game_text
        elif command == 'help':
            response = long_help_text
        elif (user_game) and user_game.check_validity(user_game.sanitize_move(command)):
            move, printed_boards = user_game.tictactoe(command)
            mid_text = mid_move_text+"\n" if printed_boards['after_computer'] else ""
            response = "".join([printed_boards['after_player'], mid_text,
                                printed_boards['after_computer'],
                                end_of_move_text[move]])
        elif (user_game) and command == 'quit':
            move = "quit"
            response = quit_game_text
        else:
            response = " ".join([unknown_message_text, short_help_text])

        if move is not None:
            if any(reset_text in move for reset_text in ("win", "draw", "quit")):
                storage.put(original_sender, None)
            elif any(keep_text == move for keep_text in ("new", "next_turn")):
                storage.put(original_sender, user_game.get_state())
            else:  # "filled" => no change, state remains the same
                pass

        bot_handler.send_message(dict(
            type = 'private',
            to = original_sender,
            subject = message['sender_email'],
            content = response,
        ))

handler_class = ticTacToeHandler

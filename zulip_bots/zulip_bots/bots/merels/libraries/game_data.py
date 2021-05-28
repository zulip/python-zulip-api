"""This serves as a bridge between the database and the other modules.

In a nutshell, this module parses a tuple from database then translates it
into a more convenient naming for easier access. It also adds certain
functions that are useful for the function of the game.
"""

from . import mechanics
from .interface import construct_grid


class GameData:
    def __init__(self, game_data=("merels", "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)):
        self.topic_name = game_data[0]
        self.turn = game_data[1]
        self.x_taken = game_data[2]
        self.o_taken = game_data[3]
        self.board = game_data[4]
        self.hill_uid = game_data[5]
        self.take_mode = game_data[6]

    def __len__(self):
        return len(self.construct())

    def construct(self):
        """Constructs a tuple based on existing records

        :return: A tuple containing all the game records
        """

        res = (
            self.topic_name,
            self.turn,
            self.x_taken,
            self.o_taken,
            self.board,
            self.hill_uid,
            self.take_mode,
        )
        return res

    def grid(self):
        """Returns the grid

        :return: A 2-dimensional 7x7 list (the grid)
        """
        return construct_grid(self.board)

    def get_x_piece_possessed_not_on_grid(self):
        """Gets the amount of X pieces that the player X still have, but not
        put yet on the grid

        :return: Amount of pieces that X has, but not on grid
        """
        return 9 - self.x_taken - mechanics.get_piece("X", self.grid())

    def get_o_piece_possessed_not_on_grid(self):
        """Gets the amount of X pieces that the player O still have, but not
        put yet on the grid

        :return: Amount of pieces that O has, but not on grid
        """

        return 9 - self.o_taken - mechanics.get_piece("O", self.grid())

    def get_phase(self):
        """Gets the phase number for the current game

        :return: A phase number (1, 2, or 3)
        """
        return mechanics.get_phase_number(
            self.grid(),
            self.turn,
            self.get_x_piece_possessed_not_on_grid(),
            self.get_o_piece_possessed_not_on_grid(),
        )

    def switch_turn(self):
        """Switches turn between X and O

        :return: None
        """
        if self.turn == "X":
            self.turn = "O"
        else:
            self.turn = "X"

    def toggle_take_mode(self):
        """Toggles take mode

        :return: None
        """
        if self.take_mode == 0:
            self.take_mode = 1
        else:
            self.take_mode = 0

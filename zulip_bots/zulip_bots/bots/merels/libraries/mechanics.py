"""Mechanics is what makes everything moves and works. It stores the game
mechanisms as well as some functions for accessing the database.
"""

from collections import Counter
from math import sqrt

from zulip_bots.game_handler import BadMoveError

from . import constants, database, game_data, interface


def is_in_grid(vertical_pos, horizontal_pos):
    """Checks whether the cell actually exists or not

    :param vertical_pos: Vertical position of the man, in int
    :param horizontal_pos: Horizontal position of the man, in int

    :return:
        True, if it exists (meaning: in the grid)
        False, if it doesn't exist (meaning: out of grid)
    """

    return [vertical_pos, horizontal_pos] in constants.ALLOWED_MOVES


def is_empty(vertical_pos, horizontal_pos, grid):
    """Checks whether the current cell is empty

    :param vertical_pos: Vertical position of the man, in int
    :param horizontal_pos: Horizontal position of the man, in int
    :param grid: A 2-dimensional 7x7 list

    :return:
        True, if it is empty
        False, if it is not empty
    """

    return grid[vertical_pos][horizontal_pos] == " "


def is_jump(vpos_before, hpos_before, vpos_after, hpos_after):
    """Checks whether the move is considered jumping

    :param vpos_before: Vertical cell location before jumping
    :param hpos_before: Horizontal cell location before jumping
    :param vpos_after: Vertical cell location after jumping
    :param hpos_after: Horizontal cell location after jumping

    :return:
        True, if it is jumping
        False, if it is not jumping
    """

    distance = sqrt((vpos_after - vpos_before) ** 2 + (hpos_after - hpos_before) ** 2)

    # If the man is in outer square, the distance must be 3 or 1
    if [vpos_before, hpos_before] in constants.OUTER_SQUARE:
        return distance not in (3, 1)

    # If the man is in middle square, the distance must be 2 or 1
    if [vpos_before, hpos_before] in constants.MIDDLE_SQUARE:
        return distance not in (2, 1)

    # If the man is in inner square, the distance must be only 1
    if [vpos_before, hpos_before] in constants.INNER_SQUARE:
        return distance != 1


def get_hills_numbers(grid):
    """Checks for hills, if it exists, get its relative position based on
    constants.py

    :param grid: A 7x7 2 dimensional grid

    :return: A string, containing the relative position of hills based on
            constants.py
    """

    relative_hills = ""
    for k, hill in enumerate(constants.HILLS):
        v1, h1 = hill[0][0], hill[0][1]
        v2, h2 = hill[1][0], hill[1][1]
        v3, h3 = hill[2][0], hill[2][1]
        if all(x == "O" for x in (grid[v1][h1], grid[v2][h2], grid[v3][h3])) or all(
            x == "X" for x in (grid[v1][h1], grid[v2][h2], grid[v3][h3])
        ):
            relative_hills += str(k)

    return relative_hills


def move_man_legal(v1, h1, v2, h2, grid):
    """Moves a man into a specified cell, assuming it is a legal move

    :param v1: Vertical position of cell
    :param h1: Horizontal position of cell
    :param v2: Vertical position of cell
    :param h2: Horizontal version of cell
    :param grid: A 2-dimensional 7x7 list
    :return: None, since grid is mutable
    """

    grid[v2][h2] = grid[v1][h1]
    grid[v1][h1] = " "


def put_man_legal(turn, v, h, grid):
    """Puts a man into specified cell, assuming it is a legal move

    :param turn: "X" or "O"
    :param v: Vertical position of cell
    :param h: Horizontal position of cell
    :param grid: A 2-dimensional 7x7 grid
    :return: None, since grid is mutable
    """

    grid[v][h] = turn


def take_man_legal(v, h, grid):
    """Takes an opponent's man from a specified cell.

    :param v: Vertical position of the cell
    :param h: Horizontal position of the cell
    :param grid: A 2-dimensional 7x7 list
    :return: None, since grid is mutable
    """

    grid[v][h] = " "


def is_legal_move(v1, h1, v2, h2, turn, phase, grid):
    """Determines whether the current move is legal or not

    :param v1: Vertical position of man
    :param h1: Horizontal position of man
    :param v2: Vertical position of man
    :param h2: Horizontal position of man
    :param turn: "X" or "O"
    :param phase: Current phase of the game
    :param grid: A 2-dimensional 7x7 list
    :return: True if it is legal, False it is not legal
    """

    if phase == 1:
        return False  # Place all the pieces first before moving one

    if phase == 3 and get_piece(turn, grid) == 3:
        return is_in_grid(v2, h2) and is_empty(v2, h2, grid) and is_own_piece(v1, h1, turn, grid)

    return (
        is_in_grid(v2, h2)
        and is_empty(v2, h2, grid)
        and not is_jump(v1, h1, v2, h2)
        and is_own_piece(v1, h1, turn, grid)
    )


def is_own_piece(v, h, turn, grid):
    """Check if the player is using the correct piece

    :param v: Vertical position of man
    :param h: Horizontal position of man
    :param turn: "X" or "O"
    :param grid: A 2-dimensional 7x7 list
    :return: True, if the player is using their own piece, False if otherwise.
    """

    return grid[v][h] == turn


def is_legal_put(v, h, grid, phase_number):
    """Determines whether putting the man in specified cell location is legal
    or not

    :param v: Vertical position of man
    :param h: Horizontal position of man
    :param grid: A 2-dimensional 7x7 list
    :param phase_number: 1, 2, or 3
    :return: True if it is legal, False if it is not legal
    """
    return is_in_grid(v, h) and is_empty(v, h, grid) and phase_number == 1


def is_legal_take(v, h, turn, grid, take_mode):
    """Determines whether taking a man in that cell is legal or not

    :param v: Vertical position of man
    :param h: Horizontal position of man
    :param turn: "X" or "O"
    :param grid: A 2-dimensional 7x7 list
    :param take_mode: 1 or 0
    :return: True if it is legal, False if it is not legal
    """

    return (
        is_in_grid(v, h)
        and not is_empty(v, h, grid)
        and not is_own_piece(v, h, turn, grid)
        and take_mode == 1
    )


def get_piece(turn, grid):
    """Counts the current piece on the grid

    :param turn: "X" or "O"
    :param grid: A 2-dimensional 7x7 list
    :return: Number of pieces of "turn" on the grid
    """

    grid_combined = []

    for row in grid:
        grid_combined += row

    counter = Counter(tuple(grid_combined))

    return counter[turn]


def who_won(topic_name, merels_storage):
    """Who won the game? If there was any at that moment

    :param topic_name: Topic name
    :param merels_storage: Merels' storage
    :return: "None", if there is no one, "X" if X is winning, "O" if O
            is winning
    """

    merels = database.MerelsStorage(topic_name, merels_storage)
    data = game_data.GameData(merels.get_game_data(topic_name))

    if data.get_phase() > 1:
        if get_piece("X", data.grid()) <= 2:
            return "O"

        if get_piece("O", data.grid()) <= 2:
            return "X"

    return "None"


def get_phase_number(grid, turn, x_pieces_possessed_not_on_grid, o_pieces_possessed_not_on_grid):
    """Updates current game phase

    :param grid: A 2-dimensional 7x7 list
    :param turn: "X" or "O"
    :param x_pieces_possessed_not_on_grid: Amount of man that X currently have,
    but not placed yet
    :param o_pieces_possessed_not_on_grid: Amount of man that O currently have,
    but not placed yet
    :return: Phase number. 1 is "placing pieces", 2 is "moving pieces", and 3
    is "flying"
    """

    if x_pieces_possessed_not_on_grid != 0 or o_pieces_possessed_not_on_grid != 0:
        # Placing pieces
        return 1
    elif get_piece("X", grid) <= 3 or get_piece("O", grid) <= 3:
        # Flying
        return 3
    else:
        # Moving pieces
        return 2


def create_room(topic_name, merels_storage):
    """Creates a game in current topic

    :param topic_name: Topic name
    :param merels_storage: Merels' storage
    :return: A response string
    """
    merels = database.MerelsStorage(topic_name, merels_storage)

    if merels.create_new_game(topic_name):
        response = ""
        response += f"A room has been created in {topic_name}. Starting game now.\n"
        response += display_game(topic_name, merels_storage)

        return response
    else:
        return (
            f"Failed: Cannot create an already existing game in {topic_name}. "
            "Please finish the game first."
        )


def display_game(topic_name, merels_storage):
    """Displays the current layout of the game, with additional info such as
    phase number and turn.

    :param topic_name: Topic name
    :param merels_storage:  Merels' storage
    :return: A response string
    """
    merels = database.MerelsStorage(topic_name, merels_storage)

    data = game_data.GameData(merels.get_game_data(topic_name))

    response = ""

    take = "Yes" if data.take_mode == 1 else "No"

    response += interface.graph_grid(data.grid()) + "\n"
    response += f"""Phase {data.get_phase()}. Take mode: {take}.
X taken: {data.x_taken}, O taken: {data.o_taken}.
    """

    return response


def reset_game(topic_name, merels_storage):
    """Resets the game in current topic

    :param topic_name: Topic name
    :param merels_storage: Merels' storage
    :return: A response string
    """
    merels = database.MerelsStorage(topic_name, merels_storage)

    merels.remove_game(topic_name)
    return "Game removed.\n" + create_room(topic_name, merels_storage) + "Game reset.\n"


def move_man(topic_name, p1, p2, merels_storage):
    """Moves the current man in topic_name from p1 to p2

    :param topic_name: Topic name
    :param p1: First cell location
    :param p2: Second cell location
    :param merels_storage: Merels' storage
    :return: A response string
    """
    merels = database.MerelsStorage(topic_name, merels_storage)
    data = game_data.GameData(merels.get_game_data(topic_name))

    # Get the grid
    grid = data.grid()

    # Check legal move
    if is_legal_move(p1[0], p1[1], p2[0], p2[1], data.turn, data.get_phase(), data.grid()):
        # Move the man
        move_man_legal(p1[0], p1[1], p2[0], p2[1], grid)
        # Construct the board back from updated grid
        board = interface.construct_board(grid)
        # Insert/update the current board
        data.board = board
        # Update the game data
        merels.update_game(
            data.topic_name,
            data.turn,
            data.x_taken,
            data.o_taken,
            data.board,
            data.hill_uid,
            data.take_mode,
        )
        return f"Moved a man from ({p1[0]}, {p1[1]}) -> ({p2[0]}, {p2[1]}) for {data.turn}."
    else:
        raise BadMoveError("Failed: That's not a legal move. Please try again.")


def put_man(topic_name, v, h, merels_storage):
    """Puts a man into the specified cell in topic_name

    :param topic_name: Topic name
    :param v: Vertical position of cell
    :param h: Horizontal position of cell
    :param merels_storage: MerelsDatabase object
    :return: A response string
    """
    merels = database.MerelsStorage(topic_name, merels_storage)
    data = game_data.GameData(merels.get_game_data(topic_name))

    # Get the grid
    grid = data.grid()

    # Check legal put
    if is_legal_put(v, h, grid, data.get_phase()):
        # Put the man
        put_man_legal(data.turn, v, h, grid)
        # Construct the board back from updated grid
        board = interface.construct_board(grid)
        # Insert/update form current board
        data.board = board
        # Update the game data
        merels.update_game(
            data.topic_name,
            data.turn,
            data.x_taken,
            data.o_taken,
            data.board,
            data.hill_uid,
            data.take_mode,
        )
        return f"Put a man to ({v}, {h}) for {data.turn}."
    else:
        raise BadMoveError("Failed: That's not a legal put. Please try again.")


def take_man(topic_name, v, h, merels_storage):
    """Takes a man from the grid

    :param topic_name: Topic name
    :param v: Vertical position of cell
    :param h: Horizontal position of cell
    :param merels_storage: Merels' storage
    :return: A response string
    """
    merels = database.MerelsStorage(topic_name, merels_storage)
    data = game_data.GameData(merels.get_game_data(topic_name))

    # Get the grid
    grid = data.grid()

    # Check legal put
    if is_legal_take(v, h, data.turn, grid, data.take_mode):
        # Take the man
        take_man_legal(v, h, grid)

        if data.turn == "X":
            data.o_taken += 1
        else:
            data.x_taken += 1

        # Construct the board back from updated grid
        board = interface.construct_board(grid)
        # Insert/update form current board
        data.board = board
        # Update the game data
        merels.update_game(
            data.topic_name,
            data.turn,
            data.x_taken,
            data.o_taken,
            data.board,
            data.hill_uid,
            data.take_mode,
        )
        return f"Taken a man from ({v}, {h}) for {data.turn}."
    else:
        raise BadMoveError("Failed: That's not a legal take. Please try again.")


def update_hill_uid(topic_name, merels_storage):
    """Updates the hill_uid then store it to the database

    :param topic_name: Topic name
    :param merels_storage: Merels' storage
    :return: None
    """

    merels = database.MerelsStorage(topic_name, merels_storage)
    data = game_data.GameData(merels.get_game_data(topic_name))

    data.hill_uid = get_hills_numbers(data.grid())

    merels.update_game(
        data.topic_name,
        data.turn,
        data.x_taken,
        data.o_taken,
        data.board,
        data.hill_uid,
        data.take_mode,
    )


def update_change_turn(topic_name, merels_storage):
    """Changes the turn of player, from X to O and from O to X

    :param topic_name: Topic name
    :param merels_storage: Merels' storage
    :return: None
    """

    merels = database.MerelsStorage(topic_name, merels_storage)
    data = game_data.GameData(merels.get_game_data(topic_name))

    data.switch_turn()

    merels.update_game(
        data.topic_name,
        data.turn,
        data.x_taken,
        data.o_taken,
        data.board,
        data.hill_uid,
        data.take_mode,
    )


def update_toggle_take_mode(topic_name, merels_storage):
    """Toggle take_mode from 0 to 1 and from 1 to 0

    :param topic_name: Topic name
    :param merels_storage: Merels' storage
    :return: None
    """

    merels = database.MerelsStorage(topic_name, merels_storage)
    data = game_data.GameData(merels.get_game_data(topic_name))

    data.toggle_take_mode()

    merels.update_game(
        data.topic_name,
        data.turn,
        data.x_taken,
        data.o_taken,
        data.board,
        data.hill_uid,
        data.take_mode,
    )


def get_take_status(topic_name, merels_storage):
    """Gets the take status

    :param topic_name: Topic name
    :param merels_storage: Merels' storage
    :return: 1 or 0
    """

    merels = database.MerelsStorage(topic_name, merels_storage)
    data = game_data.GameData(merels.get_game_data(topic_name))

    return data.take_mode


def can_take_mode(topic_name, merels_storage):
    """Check if current turn can trigger take mode.

    This process can be thought of as seeing the differences between previous
    hill_uid and current hill_uid.

    Previous hill_uid can be obtained before updating the hill_uid, and current
    hill_uid can be obtained after updating the grid.

    If the differences and length decreases after, then it is not possible that
    he player forms a new hill.

    If the differences or length increases, it is possible that the player that
    makes the move forms a new hill. This
    essentially triggers the take mode, as the player must take one opponent's
    piece from the grid.

    Essentially, how this works is by checking an updated, but not fully
    finished complete database. So the differences between hill_uid can be
    seen.

    :param topic_name: Topic name
    :param merels_storage: Merels' storage
    :return: True if this turn can trigger take mode, False if otherwise
    """

    merels = database.MerelsStorage(topic_name, merels_storage)
    data = game_data.GameData(merels.get_game_data(topic_name))

    current_hill_uid = data.hill_uid

    updated_grid = data.grid()

    updated_hill_uid = get_hills_numbers(updated_grid)

    return bool(
        current_hill_uid != updated_hill_uid and len(updated_hill_uid) >= len(current_hill_uid)
    )


def check_moves(turn, grid):
    """Checks whether the player can make any moves from specified grid and turn

    :param turn: "X" or "O"
    :param grid: A 2-dimensional 7x7 list
    :return: True, if there is any, False if otherwise
    """
    for hill in constants.HILLS:
        for k in range(2):
            g1 = grid[hill[k][0]][hill[k][1]]
            g2 = grid[hill[k + 1][0]][hill[k + 1][1]]
            if (g1 == " " and g2 == turn) or (g2 == " " and g1 == turn):
                return True

    return False


def can_make_any_move(topic_name, merels_storage):
    """Checks whether the player can actually make a move. If it is phase 1,
    don't check it and return True instead

    :param topic_name: Topic name
    :param merels_storage: Merels' storage
    :return: True if the player has a way, False if there isn't
    """

    merels = database.MerelsStorage(topic_name, merels_storage)
    data = game_data.GameData(merels.get_game_data(topic_name))

    if data.get_phase() != 1:
        return check_moves(data.turn, data.grid())

    return True

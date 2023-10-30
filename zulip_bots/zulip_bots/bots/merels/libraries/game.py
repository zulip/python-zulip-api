"""This is the main component of the game, the core of the game that squishes
everything together and make the game work. Usually user can just import this
module and use the beat() function and everything will be fine, but will there
be any certain things that can't be accomplished that way, the user may also
freely import another modules.
"""

import re

from zulip_bots.game_handler import BadMoveError

from . import database, mechanics

COMMAND_PATTERN = re.compile("^(\\w*).*(\\d,\\d).*(\\d,\\d)|^(\\w+).*(\\d,\\d)")


def get_info():
    """Gets the info on starting the game

    :return: Info on how to start the game
    """
    return "To start a game, mention me and add `create`. A game will start in that topic. "


def get_help():
    """Gets the help message

    :return: Help message
    """

    return """Commands:
put (v,h): Put a man into the grid in phase 1
move (v,h) -> (v,h): Moves a man from one point to -> another point
take (v,h): Take an opponent's man from the grid in phase 2/3

v: vertical position of grid
h: horizontal position of grid"""


def unknown_command():
    """Returns an unknown command info

    :return: A string containing info about available commands
    """
    message = "Unknown command. Available commands: put (v,h), take (v,h), move (v,h) -> (v,h)"
    raise BadMoveError(message)


def beat(message, topic_name, merels_storage):
    """This gets triggered every time a user send a message in any topic
    :param message: User's message
    :param topic_name: User's current topic
    :param merels_storage: Merels' storage
    :return: a tuple of response string and message, non-empty string
             we want to keep the turn of the same played,
             an empty string otherwise.
    """
    database.MerelsStorage(topic_name, merels_storage)
    match = COMMAND_PATTERN.match(message)
    same_player_move = ""  # message indicating move of the same player

    if match is None:
        return unknown_command()
    if match.group(1) is not None and match.group(2) is not None and match.group(3) is not None:
        responses = ""
        command = match.group(1)

        if command.lower() == "move":
            p1 = [int(x) for x in match.group(2).split(",")]
            p2 = [int(x) for x in match.group(3).split(",")]

            if mechanics.get_take_status(topic_name, merels_storage) == 1:
                raise BadMoveError("Take is required to proceed. Please try again.\n")

            responses += mechanics.move_man(topic_name, p1, p2, merels_storage) + "\n"
            no_moves = after_event_checkup(responses, topic_name, merels_storage)

            mechanics.update_hill_uid(topic_name, merels_storage)

            responses += mechanics.display_game(topic_name, merels_storage) + "\n"

            if no_moves != "":
                same_player_move = no_moves

        else:
            return unknown_command()

        if mechanics.get_take_status(topic_name, merels_storage) == 1:
            same_player_move = "Take is required to proceed.\n"
        return responses, same_player_move

    elif match.group(4) is not None and match.group(5) is not None:
        command = match.group(4)
        p1 = [int(x) for x in match.group(5).split(",")]

        # put 1,2
        if command == "put":
            responses = ""

            if mechanics.get_take_status(topic_name, merels_storage) == 1:
                raise BadMoveError("Take is required to proceed. Please try again.\n")
            responses += mechanics.put_man(topic_name, p1[0], p1[1], merels_storage) + "\n"
            no_moves = after_event_checkup(responses, topic_name, merels_storage)

            mechanics.update_hill_uid(topic_name, merels_storage)

            responses += mechanics.display_game(topic_name, merels_storage) + "\n"

            if no_moves != "":
                same_player_move = no_moves
            if mechanics.get_take_status(topic_name, merels_storage) == 1:
                same_player_move = "Take is required to proceed.\n"
            return responses, same_player_move
        # take 5,3
        elif command == "take":
            responses = ""
            if mechanics.get_take_status(topic_name, merels_storage) == 1:
                responses += mechanics.take_man(topic_name, p1[0], p1[1], merels_storage) + "\n"
                if "Failed" in responses:
                    raise BadMoveError(responses)
                mechanics.update_toggle_take_mode(topic_name, merels_storage)
                no_moves = after_event_checkup(responses, topic_name, merels_storage)

                mechanics.update_hill_uid(topic_name, merels_storage)

                responses += mechanics.display_game(topic_name, merels_storage) + "\n"
                responses += check_win(topic_name, merels_storage)

                if no_moves != "":
                    same_player_move = no_moves
                return responses, same_player_move
            else:
                raise BadMoveError("Taking is not possible.")
        else:
            return unknown_command()


def check_take_mode(response, topic_name, merels_storage):
    """This checks whether the previous action can result in a take mode for
    current player. This assumes that the previous action is successful and not
    failed.

    :param response: A response string
    :param topic_name: Topic name
    :param merels_storage: Merels' storage
    :return: None
    """
    if "Failed" not in response:
        if mechanics.can_take_mode(topic_name, merels_storage):
            mechanics.update_toggle_take_mode(topic_name, merels_storage)
        else:
            mechanics.update_change_turn(topic_name, merels_storage)


def check_any_moves(topic_name, merels_storage):
    """Check whether the player can make any moves, if can't switch to another
    player

    :param topic_name: Topic name
    :param merels_storage: MerelsDatabase object
    :return: A response string
    """
    if not mechanics.can_make_any_move(topic_name, merels_storage):
        mechanics.update_change_turn(topic_name, merels_storage)
        return "Cannot make any move on the grid. Switching to previous player.\n"

    return ""


def after_event_checkup(response, topic_name, merels_storage):
    """After doing certain moves in the game, it will check for take mode
    availability and check for any possible moves

    :param response: Current response string. This is useful for checking
    any failed previous commands
    :param topic_name: Topic name
    :param merels_storage: Merels' storage
    :return: A response string
    """
    check_take_mode(response, topic_name, merels_storage)
    return check_any_moves(topic_name, merels_storage)


def check_win(topic_name, merels_storage):
    """Checks whether the current grid has a winner, if it does, finish the
    game and remove it from the database

    :param topic_name: Topic name
    :param merels_storage: Merels' storage
    :return:
    """
    merels = database.MerelsStorage(topic_name, merels_storage)

    win = mechanics.who_won(topic_name, merels_storage)
    if win != "None":
        merels.remove_game(topic_name)
        return f"{win} wins the game!"
    return ""

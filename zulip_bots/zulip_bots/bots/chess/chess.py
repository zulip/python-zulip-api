import chess
import chess.uci
import re
import copy
from typing import Any, Optional, Dict

START_REGEX = re.compile('start with other user$')
START_COMPUTER_REGEX = re.compile(
    'start as (?P<user_color>white|black) with computer'
)
MOVE_REGEX = re.compile('do (?P<move_san>.+)$')
RESIGN_REGEX = re.compile('resign$')

class ChessHandler(object):
    def usage(self) -> str:
        return (
            'Chess Bot is a bot that allows you to play chess against either '
            'another user or the computer. Use `start with other user` or '
            '`start as <color> with computer` to start a game.\n\n'
            'In order to play against a computer, `chess.conf` must be set '
            'with the key `stockfish_location` set to the location of the '
            'Stockfish program on this computer.'
        )

    def initialize(self, bot_handler: Any) -> None:
        self.config_info = bot_handler.get_config_info('chess')

        try:
            self.engine = chess.uci.popen_engine(
                self.config_info['stockfish_location']
            )
            self.engine.uci()
        except FileNotFoundError:
            # It is helpful to allow for fake Stockfish locations if the bot
            # runner is testing or knows they won't be using an engine.
            print('That Stockfish doesn\'t exist. Continuing.')

    def handle_message(
        self,
        message: Dict[str, str],
        bot_handler: Any
    ) -> None:
        content = message['content']

        if content == '':
            bot_handler.send_reply(message, self.usage())
            return

        start_regex_match = START_REGEX.match(content)
        start_computer_regex_match = START_COMPUTER_REGEX.match(content)
        move_regex_match = MOVE_REGEX.match(content)
        resign_regex_match = RESIGN_REGEX.match(content)

        is_with_computer = False
        last_fen = chess.Board().fen()

        if bot_handler.storage.contains('is_with_computer'):
            is_with_computer = (
                # `bot_handler`'s `storage` only accepts `str` values.
                bot_handler.storage.get('is_with_computer') == str(True)
            )

        if bot_handler.storage.contains('last_fen'):
            last_fen = bot_handler.storage.get('last_fen')

        if start_regex_match:
            self.start(message, bot_handler)
        elif start_computer_regex_match:
            self.start_computer(
                message,
                bot_handler,
                start_computer_regex_match.group('user_color') == 'white'
            )
        elif move_regex_match:
            if is_with_computer:
                self.move_computer(
                    message,
                    bot_handler,
                    last_fen,
                    move_regex_match.group('move_san')
                )
            else:
                self.move(
                    message,
                    bot_handler,
                    last_fen,
                    move_regex_match.group('move_san')
                )
        elif resign_regex_match:
            self.resign(
                message,
                bot_handler,
                last_fen
            )

    def start(self, message: Dict[str, str], bot_handler: Any) -> None:
        """Starts a game with another user, with the current user as white.
        Replies to the bot handler.

        Parameters:
             - message: The Zulip Bots message object.
             - bot_handler: The Zulip Bots bot handler object.
        """
        new_board = chess.Board()
        bot_handler.send_reply(
            message,
            make_start_reponse(new_board)
        )

        # `bot_handler`'s `storage` only accepts `str` values.
        bot_handler.storage.put('is_with_computer', str(False))

        bot_handler.storage.put('last_fen', new_board.fen())

    def start_computer(
        self,
        message: Dict[str, str],
        bot_handler: Any,
        is_white_user: bool
    ) -> None:
        """Starts a game with the computer. Replies to the bot handler.

        Parameters:
             - message: The Zulip Bots message object.
             - bot_handler: The Zulip Bots bot handler object.
             - is_white_user: Whether or not the player wants to be
                                     white. If false, the user is black. If the
                                     user is white, they will get to make the
                                     first move; if they are black the computer
                                     will make the first move.
        """
        new_board = chess.Board()

        if is_white_user:
            bot_handler.send_reply(
                message,
                make_start_computer_reponse(new_board)
            )

            # `bot_handler`'s `storage` only accepts `str` values.
            bot_handler.storage.put('is_with_computer', str(True))

            bot_handler.storage.put('last_fen', new_board.fen())
        else:
            self.move_computer_first(
                message,
                bot_handler,
                new_board.fen(),
            )

    def validate_board(
        self,
        message: Dict[str, str],
        bot_handler: Any,
        fen: str
    ) -> Optional[chess.Board]:
        """Validates a board based on its FEN string. Replies to the bot
        handler if there is an error with the board.

        Parameters:
             - message: The Zulip Bots message object.
             - bot_handler: The Zulip Bots bot handler object.
             - fen: The FEN string of the board.

        Returns: `None` if the board didn't pass, or the board object itself
                 if it did.
        """
        try:
            last_board = chess.Board(fen)
        except ValueError:
            bot_handler.send_reply(
                message,
                make_copied_wrong_response()
            )
            return None

        return last_board

    def validate_move(
        self,
        message: Dict[str, str],
        bot_handler: Any,
        last_board: chess.Board,
        move_san: str,
        is_computer: object
    ) -> Optional[chess.Move]:
        """Validates a move based on its SAN string and the current board.
        Replies to the bot handler if there is an error with the move.

        Parameters:
             - message: The Zulip Bots message object.
             - bot_handler: The Zulip Bots bot handler object.
             - last_board: The board object before the move.
             - move_san: The SAN of the move.
             - is_computer: Whether or not the user is playing against a
                            computer (used in the response if the move is not
                            legal).

        Returns: `False` if the move didn't pass, or the move object itself if
                 it did.
        """
        try:
            move = last_board.parse_san(move_san)
        except ValueError:
            bot_handler.send_reply(
                message,
                make_not_legal_response(
                    last_board,
                    move_san
                )
            )
            return None

        if move not in last_board.legal_moves:
            bot_handler.send_reply(
                message,
                make_not_legal_response(last_board, move_san)
            )
            return None

        return move

    def check_game_over(
        self,
        message: Dict[str, str],
        bot_handler: Any,
        new_board: chess.Board
    ) -> bool:
        """Checks if a game is over due to
         - checkmate,
         - stalemate,
         - insufficient material,
         - 50 moves without a capture or pawn move, or
         - 3-fold repetition.
        Replies to the bot handler if it is game over.

        Parameters:
             - message: The Zulip Bots message object.
             - bot_handler: The Zulip Bots bot handler object.
             - new_board: The board object.

        Returns: True if it is game over, false if it's not.
        """
        # This assumes that the players will claim a draw after 3-fold
        # repetition or 50 moves go by without a capture or pawn move.
        # According to the official rules, the game is only guaranteed to
        # be over if it's  *5*-fold or *75* moves, but if either player
        # wants the game to be a draw, after 3 or 75 it a draw. For now,
        # just assume that the players would want the draw.
        if new_board.is_game_over(True):
            game_over_output = ''

            if new_board.is_checkmate():
                game_over_output = make_loss_response(
                    new_board,
                    'was checkmated'
                )
            elif new_board.is_stalemate():
                game_over_output = make_draw_response('stalemate')
            elif new_board.is_insufficient_material():
                game_over_output = make_draw_response(
                    'insufficient material'
                )
            elif new_board.can_claim_fifty_moves():
                game_over_output = make_draw_response(
                    '50 moves without a capture or pawn move'
                )
            elif new_board.can_claim_threefold_repetition():
                game_over_output = make_draw_response('3-fold repetition')

            bot_handler.send_reply(
                message,
                game_over_output
            )

            return True

        return False

    def move(
        self,
        message: Dict[str, str],
        bot_handler: Any,
        last_fen: str,
        move_san: str
    ) -> None:
        """Makes a move for a user in a game with another user. Replies to
        the bot handler.

        Parameters:
             - message: The Zulip Bots message object.
             - bot_handler: The Zulip Bots bot handler object.
             - last_fen: The FEN string of the board before the move.
             - move_san: The SAN of the move to make.
        """
        last_board = self.validate_board(message, bot_handler, last_fen)

        if not last_board:
            return

        move = self.validate_move(
            message,
            bot_handler,
            last_board,
            move_san,
            False
        )

        if not move:
            return

        new_board = copy.copy(last_board)
        new_board.push(move)

        if self.check_game_over(message, bot_handler, new_board):
            return

        bot_handler.send_reply(
            message,
            make_move_reponse(last_board, new_board, move)
        )

        bot_handler.storage.put('last_fen', new_board.fen())

    def move_computer(
        self,
        message: Dict[str, str],
        bot_handler: Any,
        last_fen: str,
        move_san: str
    ) -> None:
        """Preforms a move for a user in a game with the computer and then
        makes the computer's move. Replies to the bot handler. Unlike `move`,
        replies only once to the bot handler every two moves (only after the
        computer moves) instead of after every move. Doesn't require a call in
        order to make the computer move. To make the computer move without the
        user going first, use `move_computer_first`.

        Parameters:
             - message: The Zulip Bots message object.
             - bot_handler: The Zulip Bots bot handler object.
             - last_fen: The FEN string of the board before the user's move.
             - move_san: The SAN of the user's move to make.
        """
        last_board = self.validate_board(message, bot_handler, last_fen)

        if not last_board:
            return

        move = self.validate_move(
            message,
            bot_handler,
            last_board,
            move_san,
            True
        )

        if not move:
            return

        new_board = copy.copy(last_board)
        new_board.push(move)

        if self.check_game_over(message, bot_handler, new_board):
            return

        computer_move = calculate_computer_move(
            new_board,
            self.engine
        )

        new_board_after_computer_move = copy.copy(new_board)
        new_board_after_computer_move.push(computer_move)

        if self.check_game_over(
            message,
            bot_handler,
            new_board_after_computer_move
        ):
            return

        bot_handler.send_reply(
            message,
            make_move_reponse(
                new_board,
                new_board_after_computer_move,
                computer_move
            )
        )

        bot_handler.storage.put(
            'last_fen',
            new_board_after_computer_move.fen()
        )

    def move_computer_first(
        self,
        message: Dict[str, str],
        bot_handler: Any,
        last_fen: str
    ) -> None:
        """Preforms a move for the computer without having the user go first in
        a game with the computer. Replies to the bot handler. Like
        `move_computer`, but doesn't have the user move first. This is usually
        only useful at the beginning of a game.

        Parameters:
             - message: The Zulip Bots message object.
             - bot_handler: The Zulip Bots bot handler object.
             - last_fen: The FEN string of the board before the computer's
                         move.
        """
        last_board = self.validate_board(message, bot_handler, last_fen)

        computer_move = calculate_computer_move(
            last_board,
            self.engine
        )

        new_board_after_computer_move = copy.copy(last_board)  # type: chess.Board
        new_board_after_computer_move.push(computer_move)

        if self.check_game_over(
            message,
            bot_handler,
            new_board_after_computer_move
        ):
            return

        bot_handler.send_reply(
            message,
            make_move_reponse(
                last_board,
                new_board_after_computer_move,
                computer_move
            )
        )

        bot_handler.storage.put(
            'last_fen',
            new_board_after_computer_move.fen()
        )

        # `bot_handler`'s `storage` only accepts `str` values.
        bot_handler.storage.put('is_with_computer', str(True))

    def resign(
        self,
        message: Dict[str, str],
        bot_handler: Any,
        last_fen: str
    ) -> None:
        """Resigns the game for the current player.

        Parameters:
             - message: The Zulip Bots message object.
             - bot_handler: The Zulip Bots bot handler object.
             - last_fen: The FEN string of the board.
        """
        last_board = self.validate_board(message, bot_handler, last_fen)

        if not last_board:
            return

        bot_handler.send_reply(
            message,
            make_loss_response(last_board, 'resigned')
        )

handler_class = ChessHandler

def calculate_computer_move(board: chess.Board, engine: Any) -> chess.Move:
    """Calculates the computer's move.

    Parameters:
         - board: The board object before the move.
         - engine: The UCI engine object.

    Returns: The computer's move object.
    """
    engine.position(board)
    best_move_and_ponder_move = engine.go(movetime=(3000))
    return best_move_and_ponder_move[0]

def make_draw_response(reason: str) -> str:
    """Makes a response string for a draw.

    Parameters:
         - reason: The reason for the draw, in the form of a noun, e.g.,
                   'stalemate' or 'insufficient material'.

    Returns: The draw response string.
    """
    return 'It\'s a draw because of {}!'.format(reason)

def make_loss_response(board: chess.Board, reason: str) -> str:
    """Makes a response string for a loss (or win).

    Parameters:
         - board: The board object at the end of the game.
         - reason: The reason for the loss, in the form of a predicate, e.g.,
                   'was checkmated'.

    Returns: The loss response string.
    """
    return (
        '*{}* {}. **{}** wins!\n\n'
        '{}'
    ).format(
        'White' if board.turn else 'Black',
        reason,
        'Black' if board.turn else 'White',
        make_str(board, board.turn)
    )

def make_not_legal_response(board: chess.Board, move_san: str) -> str:
    """Makes a response string for a not-legal move.

    Parameters:
         - board: The board object before the move.
         - move_san: The SAN of the not-legal move.

    Returns: The not-legal-move response string.
    """
    return (
        'Sorry, the move *{}* isn\'t legal.\n\n'
        '{}'
        '\n\n\n'
        '{}'
    ).format(
        move_san,
        make_str(board, board.turn),
        make_footer()
    )

def make_copied_wrong_response() -> str:
    """Makes a response string for a FEN string that was copied wrong.

    Returns: The copied-wrong response string.
    """
    return (
        'Sorry, it seems like you copied down the response wrong.\n\n'
        'Please try to copy the response again from the last message!'
    )

def make_start_reponse(board: chess.Board) -> str:
    """Makes a response string for the first response of a game with another
    user.

    Parameters:
         - board: The board object to start the game with (which most-likely
                  should be general opening chess position).

    Returns: The starting response string.
    """
    return (
        'New game! The board looks like this:\n\n'
        '{}'
        '\n\n\n'
        'Now it\'s **{}**\'s turn.'
        '\n\n\n'
        '{}'
    ).format(
        make_str(board, True),
        'white' if board.turn else 'black',
        make_footer()
    )

def make_start_computer_reponse(board: chess.Board) -> str:
    """Makes a response string for the first response of a game with a
    computer, when the user is playing as white. If the user is playing as
    black, use `ChessHandler.move_computer_first`.

    Parameters:
         - board: The board object to start the game with (which most-likely
                  should be general opening chess position).

    Returns: The starting response string.
    """
    return (
        'New game with computer! The board looks like this:\n\n'
        '{}'
        '\n\n\n'
        'Now it\'s **{}**\'s turn.'
        '\n\n\n'
        '{}'
    ).format(
        make_str(board, True),
        'white' if board.turn else 'black',
        make_footer()
    )

def make_move_reponse(
    last_board: chess.Board,
    new_board: chess.Board,
    move: chess.Move
) -> str:
    """Makes a response string for after a move is made.

    Parameters:
         - last_board: The board object before the move.
         - new_board: The board object after the move.
         - move: The move object.

    Returns: The move response string.
    """
    return (
        'The board was like this:\n\n'
        '{}'
        '\n\n\n'
        'Then *{}* moved *{}*:\n\n'
        '{}'
        '\n\n\n'
        'Now it\'s **{}**\'s turn.'
        '\n\n\n'
        '{}'
    ).format(
        make_str(last_board, new_board.turn),
        'white' if last_board.turn else 'black',
        last_board.san(move),
        make_str(new_board, new_board.turn),
        'white' if new_board.turn else 'black',
        make_footer()
    )

def make_footer() -> str:
    """Makes a footer to be appended to the bottom of other, actionable
    responses.
    """
    return (
        'To make your next move, respond to Chess Bot with\n\n'
        '```do <your move>```\n\n'
        '*Remember to @-mention Chess Bot at the beginning of your '
        'response.*'
    )

def make_str(board: chess.Board, is_white_on_bottom: bool) -> str:
    """Converts a board object into a string to be used in Markdown. Backticks
    are added around the string to preserve formatting.

    Parameters:
         - board: The board object.
         - is_white_on_bottom: Whether or not white should be on the bottom
                               side in the string. If false, black will be on
                               the bottom.

    Returns: The string made from the board.
    """
    default_str = board.__str__()

    replaced_str = replace_with_unicode(default_str)
    replaced_and_guided_str = guide_with_numbers(replaced_str)
    properly_flipped_str = (
        replaced_and_guided_str if is_white_on_bottom
        else replaced_and_guided_str[::-1]
    )
    trimmed_str = trim_whitespace_before_newline(properly_flipped_str)
    monospaced_str = '```\n{}\n```'.format(trimmed_str)

    return monospaced_str

def guide_with_numbers(board_str: str) -> str:
    """Adds numbers and letters on the side of a string without them made out
    of a board.

    Parameters:
         - board_str: The string from the board object.

    Returns: The string with the numbers and letters.
    """
    # Spaces and newlines would mess up the loop because they add extra indexes
    # between pieces. Newlines are added later by the loop and spaces are added
    # back in at the end.
    board_without_whitespace_str = board_str.replace(' ', '').replace('\n', '')

    # The first number, 8, needs to be added first because it comes before a
    # newline. From then on, numbers are inserted at newlines.
    row_list = list('8' + board_without_whitespace_str)

    for i, char in enumerate(row_list):
        # `(i + 1) % 10 == 0` if it is the end of a row, i.e., the 10th column
        # since lists are 0-indexed.
        if (i + 1) % 10 == 0:
            # Since `i + 1` is always a multiple of 10 (because index 0, 10,
            # 20, etc. is the other row letter and 1-8, 11-18, 21-28, etc. are
            # the squares), `(i + 1) // 10` is the inverted row number (1 when
            # it should be 8, 2 when it should be 7, etc.), so therefore
            # `9 - (i + 1) // 10` is the actual row number.
            row_num = 9 - (i + 1) // 10

            # The 3 separate components are split into only 2 elements so that
            # the newline isn't counted by the loop. If they were split into 3,
            # or combined into just 1 string, the counter would become off
            # because it would be counting what is really 2 rows as 3 or 1.
            row_list[i:i] = [str(row_num) + '\n', str(row_num - 1)]

    # 1 is appended to the end because it isn't created in the loop, and lines
    # that begin with spaces have their spaces removed for aesthetics.
    row_str = (' '.join(row_list) + ' 1').replace('\n ', '\n')

    # a, b, c, d, e, f, g, and h are easy to add in.
    row_and_col_str = (
        '  a b c d e f g h  \n' + row_str + '\n  a b c d e f g h  '
    )

    return row_and_col_str

def replace_with_unicode(board_str: str) -> str:
    """Replaces the default characters in a board object's string output with
    Unicode chess characters, e.g., '♖' instead of 'R.'

    Parameters:
         - board_str: The string from the board object.

    Returns: The string with the replaced characters.
    """
    replaced_str = board_str

    replaced_str = replaced_str.replace('P', '♙')
    replaced_str = replaced_str.replace('N', '♘')
    replaced_str = replaced_str.replace('B', '♗')
    replaced_str = replaced_str.replace('R', '♖')
    replaced_str = replaced_str.replace('Q', '♕')
    replaced_str = replaced_str.replace('K', '♔')

    replaced_str = replaced_str.replace('p', '♟')
    replaced_str = replaced_str.replace('n', '♞')
    replaced_str = replaced_str.replace('b', '♝')
    replaced_str = replaced_str.replace('r', '♜')
    replaced_str = replaced_str.replace('q', '♛')
    replaced_str = replaced_str.replace('k', '♚')

    replaced_str = replaced_str.replace('.', '·')

    return replaced_str

def trim_whitespace_before_newline(str_to_trim: str) -> str:
    """Removes any spaces before a newline in a string.

    Parameters:
         - str_to_trim: The string to trim.

    Returns: The trimmed string.
    """
    return re.sub('\s+$', '', str_to_trim, flags=re.M)

from zulip_bots.test_lib import BotTestCase

from contextlib import contextmanager
from unittest.mock import MagicMock
from zulip_bots.bots.connect_four.connect_four import *

class TestConnectFourBot(BotTestCase):
    bot_name = 'connect_four'

    def make_request_message(self, content, user='foo@example.com'):
        message = dict(
            sender_email=user,
            content=content,
        )
        return message

    # Function that serves similar purpose to BotTestCase.verify_dialog, but allows for multiple responses to be handled
    def verify_response(self, request, expected_response, response_number, data=None, computer_move=None, user = 'foo@example.com'):
        '''
        This function serves a similar purpose
        to BotTestCase.verify_dialog, but allows
        for multiple responses to be validated,
        and for mocking of the bot's internal data
        '''

        bot, bot_handler = self._get_handlers()
        message = self.make_request_message(request, user)
        bot_handler.reset_transcript()
        stash = ConnectFourModel.computer_move

        if data:
            bot.get_stored_data = MagicMock(return_value = data)

        if computer_move is not None:
            ConnectFourModel.computer_move = MagicMock(return_value = computer_move)

        bot.handle_message(message, bot_handler)

        responses = [
            message
            for (method, message)
            in bot_handler.transcript
        ]

        first_response = responses[response_number]
        self.assertEqual(expected_response, first_response['content'])

        ConnectFourModel.computer_move = stash

    def help_message(self):
        return '**Connect Four Bot Help:**\n' + \
            '*Preface all commands with @bot-name*\n\n' + \
            '* To see the current status of the game, type\n' + \
            '```status```\n' + \
            '* To start a game against the computer, type\n' + \
            '```start game with computer```\n' + \
            '* To start a game against another player, type\n' + \
            '```start game with user@example.com```\n' + \
            '* To quit a game at any time, type\n' + \
            '```quit```\n' + \
            '* To withdraw an invitation, type\n' + \
            '```cancel game```\n' +\
            '* To make your move during a game, type\n' + \
            '```move <column-number>```'

    def no_game_status(self):
        return '**Connect Four Game Status**\n' + \
            '*If you suspect users are abusing the bot, please alert the bot owner*\n\n' +\
            '**The bot is not running a game right now!**\n' +\
            'Type ```start game with user@example.com``` to start a game with another user,\n' +\
            'or type ```start game with computer``` to start a game with the computer'

    def inviting_status(self):
        return '**Connect Four Game Status**\n' +\
            '*If you suspect users are abusing the bot, please alert the bot owner*\n\n' +\
            'foo@example.com\'s invitation to play foo2@example.com' +\
            ' is still pending. Wait for the game to finish to play a game.'

    def one_player_status(self):
        return '**Connect Four Game Status**\n' +\
            '*If you suspect users are abusing the bot, please alert the bot owner*\n\n' +\
            'The bot is currently running a single player game for foo@example.com.'

    def two_player_status(self):
        return '**Connect Four Game Status**\n' +\
            '*If you suspect users are abusing the bot, please alert the bot owner*\n\n' +\
            'The bot is currently running a two player game ' +\
            'between foo@example.com and foo2@example.com.'

    blank_board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0]]

    almost_win_board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [1, -1, 0, 0, 0, 0, 0],
        [1, -1, 0, 0, 0, 0, 0],
        [1, -1, 0, 0, 0, 0, 0]]

    almost_draw_board = [
        [1, -1, 1, -1, 1, -1, 0],
        [0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, -1],
        [0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, -1],
        [0, 0, 0, 0, 0, 0, 1]]

    start_two_player_data = {'state': 'playing', 'game_type': 'two_player', 'board': blank_board, 'users': ['foo@example.com', 'foo2@example.com'], 'turn': 0}
    start_one_player_data = {'state': 'playing', 'game_type': 'one_player', 'board': blank_board, 'users': ['foo@example.com'], 'turn': 0}
    end_two_player_data = {'state': 'playing', 'game_type': 'two_player', 'board': almost_win_board, 'users': ['foo@example.com', 'foo2@example.com'], 'turn': 0}
    end_one_player_data = {'state': 'playing', 'game_type': 'one_player', 'board': almost_win_board, 'users': ['foo@example.com'], 'turn': 0}
    inviting_two_player_data = {'state': 'inviting', 'game_type': 'two_player', 'board': blank_board, 'users': ['foo@example.com', 'foo2@example.com'], 'turn': 0}
    draw_data = {'state': 'playing', 'game_type': 'one_player', 'board': almost_draw_board, 'users': ['foo@example.com', 'foo2@example.com'], 'turn': 0}

    def test_static_messages(self):
        self.verify_response('help', self.help_message(), 0)
        self.verify_response('status', self.no_game_status(), 0)
        self.verify_response('status', self.inviting_status(), 0, data=self.inviting_two_player_data)
        self.verify_response('status', self.one_player_status(), 0, data=self.start_one_player_data)
        self.verify_response('status', self.two_player_status(), 0, data=self.start_two_player_data)

    def test_start_game(self):
        self.verify_response('start game with computer', '**You started a new game with the computer!**', 0)
        self.verify_response('start game with user@example.com', 'You\'ve sent an invitation to play Connect Four with user@example.com. I\'ll let you know when they respond to the invitation', 0)
        self.verify_response('start game with foo@example.com', 'You can\'t play against yourself!', 0)

    def test_invitation(self):
        self.verify_response('accept', 'You accepted the invitation to play with foo@example.com', 0, data=self.inviting_two_player_data, user = 'foo2@example.com')
        self.verify_response('decline', 'You declined the invitation to play with foo@example.com', 0, data=self.inviting_two_player_data, user = 'foo2@example.com')
        self.verify_response('withdraw invitation', 'Your invitation to play foo2@example.com has been withdrawn', 0, data=self.inviting_two_player_data)

    def test_move(self):
        self.verify_response('move 8', 'That\'s an invalid move. Please specify a column '
                             'between 1 and 7 with at least one open spot.', 0, data=self.start_two_player_data)
        self.verify_response('move 1', 'You placed your token in column 1.', 0, data=self.start_two_player_data)
        self.verify_response('move 1', '**the Computer moved in column 1**.', 3, data=self.start_one_player_data, computer_move=0)

    def test_game_over(self):
        self.verify_response('move 1', '**Congratulations, you win! :tada:**', 2, data=self.end_two_player_data)
        self.verify_response('move 3', 'Sorry, but the Computer won :cry:', 5, data=self.end_one_player_data, computer_move=1)
        self.verify_response('move 7', '**It\'s a draw!**', 2, data = self.draw_data)

    def test_quit(self):
        self.verify_response('quit', 'Are you sure you want to quit? You will forfeit the game!\n'
                             'Type ```confirm quit``` to forfeit.', 0, data=self.start_two_player_data)
        self.verify_response('confirm quit', '**You have forfeit the game**\nSorry, but you lost :cry:', 0, data=self.start_two_player_data)

    def test_force_reset(self):
        with self.mock_config_info({'superusers': '["foo@example.com"]'}):
            self.verify_response('force reset', 'The game has been force reset', 1, data=self.start_one_player_data)

    def test_privilege_check(self):
        self.verify_response('move 4', 'Sorry, but you can\'t run the command ```move 4```', 0, data=self.inviting_two_player_data)
        self.verify_response('start game with computer', 'Sorry, but other users are already using the bot.'
                             'Type ```status``` to see the current status of the bot.', 0, data=self.inviting_two_player_data, user = 'foo3@example.com')
        self.verify_response('quit', 'Sorry, but you can\'t run the command ```quit```', 0)
        self.verify_response('accept', 'Sorry, but you can\'t run the command ```accept```', 0, data=self.end_two_player_data)
        self.verify_response('force reset', 'Sorry, but you can\'t run the command ```force reset```', 0)

    def test_connect_four_logic(self):
        def confirmAvailableMoves(good_moves, bad_moves, board):
            connectFourModel.update_board(board)

            for move in good_moves:
                self.assertTrue(connectFourModel.validate_move(move))

            for move in bad_moves:
                self.assertFalse(connectFourModel.validate_move(move))

        def confirmMove(column_number, token_number, initial_board, final_board):
            connectFourModel.update_board(initial_board)
            test_board = connectFourModel.make_move(column_number, token_number)

            self.assertEqual(test_board, final_board)

        def confirmGameOver(board, result):
            connectFourModel.update_board(board)
            game_over = connectFourModel.determine_game_over('first_player', 'second_player')

            self.assertEqual(game_over, result)

        def confirmWinStates(array):
            for board in array[0]:
                confirmGameOver(board, 'first_player')

            for board in array[1]:
                confirmGameOver(board, 'second_player')

        connectFourModel = ConnectFourModel()

        # Basic Board setups
        blank_board = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0]]

        full_board = [
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1]]

        single_column_board = [
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1]]

        diagonal_board = [
            [0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 1, 1],
            [0, 0, 0, 0, 1, 1, 1],
            [0, 0, 0, 1, 1, 1, 1],
            [0, 0, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1]]

        # Winning Board Setups
        # Each array if consists of two arrays:
        # The first stores win states for '1'
        # The second stores win state for '-1'
        # Note these are not necessarily valid board states
        # for simplicity (random -1 and 1s could be added)
        horizontal_win_boards = [
            [
                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [1, 1, 1, 1, 0, 0, 0]],

                [[0, 0, 0, 1, 1, 1, 1],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]],

                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 1, 1, 1, 1, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]]
            ],
            [
                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [-1, -1, -1, -1, 0, 0, 0]],

                [[0, 0, 0, -1, -1, -1, -1],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]],

                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, -1, -1, -1, -1, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]]
            ]
        ]

        vertical_win_boards = [
            [
                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [1, 0, 0, 0, 0, 0, 0],
                 [1, 0, 0, 0, 0, 0, 0],
                 [1, 0, 0, 0, 0, 0, 0],
                 [1, 0, 0, 0, 0, 0, 0]],

                [[0, 0, 0, 0, 0, 0, 1],
                 [0, 0, 0, 0, 0, 0, 1],
                 [0, 0, 0, 0, 0, 0, 1],
                 [0, 0, 0, 0, 0, 0, 1],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]],

                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 1, 0, 0, 0],
                 [0, 0, 0, 1, 0, 0, 0],
                 [0, 0, 0, 1, 0, 0, 0],
                 [0, 0, 0, 1, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]]
            ],
            [
                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [-1, 0, 0, 0, 0, 0, 0],
                 [-1, 0, 0, 0, 0, 0, 0],
                 [-1, 0, 0, 0, 0, 0, 0],
                 [-1, 0, 0, 0, 0, 0, 0]],

                [[0, 0, 0, 0, 0, 0, -1],
                 [0, 0, 0, 0, 0, 0, -1],
                 [0, 0, 0, 0, 0, 0, -1],
                 [0, 0, 0, 0, 0, 0, -1],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]],

                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, -1, 0, 0, 0],
                 [0, 0, 0, -1, 0, 0, 0],
                 [0, 0, 0, -1, 0, 0, 0],
                 [0, 0, 0, -1, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]]
            ]
        ]

        major_diagonal_win_boards = [
            [
                [[1, 0, 0, 0, 0, 0, 0],
                 [0, 1, 0, 0, 0, 0, 0],
                 [0, 0, 1, 0, 0, 0, 0],
                 [0, 0, 0, 1, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]],

                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 1, 0, 0, 0],
                 [0, 0, 0, 0, 1, 0, 0],
                 [0, 0, 0, 0, 0, 1, 0],
                 [0, 0, 0, 0, 0, 0, 1]],

                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 1, 0, 0, 0, 0],
                 [0, 0, 0, 1, 0, 0, 0],
                 [0, 0, 0, 0, 1, 0, 0],
                 [0, 0, 0, 0, 0, 1, 0],
                 [0, 0, 0, 0, 0, 0, 0]]
            ],
            [
                [[-1, 0, 0, 0, 0, 0, 0],
                 [0, -1, 0, 0, 0, 0, 0],
                 [0, 0, -1, 0, 0, 0, 0],
                 [0, 0, 0, -1, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]],

                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, -1, 0, 0, 0],
                 [0, 0, 0, 0, -1, 0, 0],
                 [0, 0, 0, 0, 0, -1, 0],
                 [0, 0, 0, 0, 0, 0, -1]],

                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, -1, 0, 0, 0, 0],
                 [0, 0, 0, -1, 0, 0, 0],
                 [0, 0, 0, 0, -1, 0, 0],
                 [0, 0, 0, 0, 0, -1, 0],
                 [0, 0, 0, 0, 0, 0, 0]]
            ]
        ]

        minor_diagonal_win_boards = [
            [
                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 1, 0, 0, 0],
                 [0, 0, 1, 0, 0, 0, 0],
                 [0, 1, 0, 0, 0, 0, 0],
                 [1, 0, 0, 0, 0, 0, 0]],

                [[0, 0, 0, 0, 0, 0, 1],
                 [0, 0, 0, 0, 0, 1, 0],
                 [0, 0, 0, 0, 1, 0, 0],
                 [0, 0, 0, 1, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]],

                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 1, 0, 0],
                 [0, 0, 0, 1, 0, 0, 0],
                 [0, 0, 1, 0, 0, 0, 0],
                 [0, 1, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]]
            ],
            [
                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, -1, 0, 0, 0],
                 [0, 0, -1, 0, 0, 0, 0],
                 [0, -1, 0, 0, 0, 0, 0],
                 [-1, 0, 0, 0, 0, 0, 0]],

                [[0, 0, 0, 0, 0, 0, -1],
                 [0, 0, 0, 0, 0, -1, 0],
                 [0, 0, 0, 0, -1, 0, 0],
                 [0, 0, 0, -1, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]],

                [[0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, -1, 0, 0],
                 [0, 0, 0, -1, 0, 0, 0],
                 [0, 0, -1, 0, 0, 0, 0],
                 [0, -1, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0]]
            ]
        ]

        # Test Move Validation Logic
        confirmAvailableMoves([0, 1, 2, 3, 4, 5, 6], [-1, 7], blank_board)
        confirmAvailableMoves([3], [0, 1, 2, 4, 5, 6], single_column_board)
        confirmAvailableMoves([0, 1, 2, 3, 4, 5], [6], diagonal_board)

        # Test Available Move Logic
        connectFourModel.update_board(blank_board)
        self.assertEqual(connectFourModel.available_moves(), [0, 1, 2, 3, 4, 5, 6])

        connectFourModel.update_board(single_column_board)
        self.assertEqual(connectFourModel.available_moves(), [3])

        connectFourModel.update_board(full_board)
        self.assertEqual(connectFourModel.available_moves(), [])

        # Test Move Logic
        confirmMove(0, 1, blank_board,
                    [[0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0],
                     [1, 0, 0, 0, 0, 0, 0]])

        confirmMove(0, -1, blank_board,
                    [[0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0],
                     [-1, 0, 0, 0, 0, 0, 0]])

        confirmMove(0, 1, diagonal_board,
                    [[0, 0, 0, 0, 0, 0, 1],
                     [0, 0, 0, 0, 0, 1, 1],
                     [0, 0, 0, 0, 1, 1, 1],
                     [0, 0, 0, 1, 1, 1, 1],
                     [0, 0, 1, 1, 1, 1, 1],
                     [1, 1, 1, 1, 1, 1, 1]])

        confirmMove(1, 1, diagonal_board,
                    [[0, 0, 0, 0, 0, 0, 1],
                     [0, 0, 0, 0, 0, 1, 1],
                     [0, 0, 0, 0, 1, 1, 1],
                     [0, 0, 0, 1, 1, 1, 1],
                     [0, 1, 1, 1, 1, 1, 1],
                     [0, 1, 1, 1, 1, 1, 1]])

        confirmMove(2, 1, diagonal_board,
                    [[0, 0, 0, 0, 0, 0, 1],
                     [0, 0, 0, 0, 0, 1, 1],
                     [0, 0, 0, 0, 1, 1, 1],
                     [0, 0, 1, 1, 1, 1, 1],
                     [0, 0, 1, 1, 1, 1, 1],
                     [0, 1, 1, 1, 1, 1, 1]])

        confirmMove(3, 1, diagonal_board,
                    [[0, 0, 0, 0, 0, 0, 1],
                     [0, 0, 0, 0, 0, 1, 1],
                     [0, 0, 0, 1, 1, 1, 1],
                     [0, 0, 0, 1, 1, 1, 1],
                     [0, 0, 1, 1, 1, 1, 1],
                     [0, 1, 1, 1, 1, 1, 1]])

        confirmMove(4, 1, diagonal_board,
                    [[0, 0, 0, 0, 0, 0, 1],
                     [0, 0, 0, 0, 1, 1, 1],
                     [0, 0, 0, 0, 1, 1, 1],
                     [0, 0, 0, 1, 1, 1, 1],
                     [0, 0, 1, 1, 1, 1, 1],
                     [0, 1, 1, 1, 1, 1, 1]])

        confirmMove(5, 1, diagonal_board,
                    [[0, 0, 0, 0, 0, 1, 1],
                     [0, 0, 0, 0, 0, 1, 1],
                     [0, 0, 0, 0, 1, 1, 1],
                     [0, 0, 0, 1, 1, 1, 1],
                     [0, 0, 1, 1, 1, 1, 1],
                     [0, 1, 1, 1, 1, 1, 1]])

        # Test Game Over Logic:
        confirmGameOver(blank_board, False)
        confirmGameOver(full_board, 'draw')

        # Test Win States:
        confirmWinStates(horizontal_win_boards)
        confirmWinStates(vertical_win_boards)
        confirmWinStates(major_diagonal_win_boards)
        confirmWinStates(minor_diagonal_win_boards)

        # Test Computer Move:
        connectFourModel.update_board(blank_board)
        self.assertTrue(connectFourModel.computer_move() in [0, 1, 2, 3, 4, 5, 6])

        connectFourModel.update_board(single_column_board)
        self.assertEqual(connectFourModel.computer_move(), 3)

        connectFourModel.update_board(diagonal_board)
        self.assertTrue(connectFourModel.computer_move() in [0, 1, 2, 3, 4, 5])

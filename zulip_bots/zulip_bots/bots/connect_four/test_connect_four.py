from typing import Dict, Final, List

from typing_extensions import override

from zulip_bots.bots.connect_four.controller import ConnectFourModel
from zulip_bots.game_handler import BadMoveError
from zulip_bots.test_lib import BotTestCase, DefaultTests


class TestConnectFourBot(BotTestCase, DefaultTests):
    bot_name = "connect_four"

    @override
    def make_request_message(
        self, content: str, user: str = "foo@example.com", user_name: str = "foo"
    ) -> Dict[str, str]:
        message = dict(sender_email=user, content=content, sender_full_name=user_name)
        return message

    # Function that serves similar purpose to BotTestCase.verify_dialog, but allows for multiple responses to be handled
    def verify_response(
        self,
        request: str,
        expected_response: str,
        response_number: int,
        user: str = "foo@example.com",
    ) -> None:
        """
        This function serves a similar purpose
        to BotTestCase.verify_dialog, but allows
        for multiple responses to be validated,
        and for mocking of the bot's internal data
        """

        bot, bot_handler = self._get_handlers()
        message = self.make_request_message(request, user)
        bot_handler.reset_transcript()

        bot.handle_message(message, bot_handler)

        responses = [message for (method, message) in bot_handler.transcript]

        first_response = responses[response_number]
        self.assertEqual(expected_response, first_response["content"])

    def help_message(self) -> str:
        return """** Connect Four Bot Help:**
*Preface all commands with @**test-bot***
* To start a game in a stream (*recommended*), type
`start game`
* To start a game against another player, type
`start game with @<player-name>`
* To play game with the current number of players, type
`play game`
* To quit a game at any time, type
`quit`
* To end a game with a draw, type
`draw`
* To forfeit a game, type
`forfeit`
* To see the leaderboard, type
`leaderboard`
* To withdraw an invitation, type
`cancel game`
* To see rules of this game, type
`rules`
* To make your move during a game, type
```move <column-number>``` or ```<column-number>```"""

    def test_static_responses(self) -> None:
        self.verify_response("help", self.help_message(), 0)

    def test_game_message_handler_responses(self) -> None:
        board = (
            ":one: :two: :three: :four: :five: :six: :seven:\n\n"
            "\
:white_circle: :white_circle: :white_circle: :white_circle: \
:white_circle: :white_circle: :white_circle: \n\n\
:white_circle: :white_circle: :white_circle: :white_circle: \
:white_circle: :white_circle: :white_circle: \n\n\
:white_circle: :white_circle: :white_circle: :white_circle: \
:white_circle: :white_circle: :white_circle: \n\n\
:blue_circle: :red_circle: :white_circle: :white_circle: :white_circle: \
:white_circle: :white_circle: \n\n\
:blue_circle: :red_circle: :white_circle: :white_circle: :white_circle: \
:white_circle: :white_circle: \n\n\
:blue_circle: :red_circle: :white_circle: :white_circle: :white_circle: \
:white_circle: :white_circle: "
        )
        bot, bot_handler = self._get_handlers()
        self.assertEqual(bot.game_message_handler.parse_board(self.almost_win_board), board)
        self.assertEqual(bot.game_message_handler.get_player_color(1), ":red_circle:")
        self.assertEqual(
            bot.game_message_handler.alert_move_message("foo", "move 6"), "foo moved in column 6"
        )
        self.assertEqual(
            bot.game_message_handler.game_start_message(),
            "Type `move <column-number>` or `<column-number>` to place a token.\n\
The first player to get 4 in a row wins!\n Good Luck!",
        )

    blank_board: Final = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]

    almost_win_board: Final = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [1, -1, 0, 0, 0, 0, 0],
        [1, -1, 0, 0, 0, 0, 0],
        [1, -1, 0, 0, 0, 0, 0],
    ]

    almost_draw_board: Final = [
        [1, -1, 1, -1, 1, -1, 0],
        [0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, -1],
        [0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, -1],
        [0, 0, 0, 0, 0, 0, 1],
    ]

    def test_connect_four_logic(self) -> None:
        def confirm_available_moves(
            good_moves: List[int], bad_moves: List[int], board: List[List[int]]
        ) -> None:
            connect_four_model.update_board(board)

            for move in good_moves:
                self.assertTrue(connect_four_model.validate_move(move))

            for move in bad_moves:
                self.assertFalse(connect_four_model.validate_move(move))

        def confirm_move(
            column_number: int,
            token_number: int,
            initial_board: List[List[int]],
            final_board: List[List[int]],
        ) -> None:
            connect_four_model.update_board(initial_board)
            test_board = connect_four_model.make_move("move " + str(column_number), token_number)

            self.assertEqual(test_board, final_board)

        def confirm_game_over(board: List[List[int]], result: str) -> None:
            connect_four_model.update_board(board)
            game_over = connect_four_model.determine_game_over(["first_player", "second_player"])

            self.assertEqual(game_over, result)

        def confirm_win_states(array: List[List[List[List[int]]]]) -> None:
            for board in array[0]:
                confirm_game_over(board, "first_player")

            for board in array[1]:
                confirm_game_over(board, "second_player")

        connect_four_model = ConnectFourModel()

        # Basic Board setups
        blank_board = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]

        full_board = [
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
        ]

        single_column_board = [
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1],
        ]

        diagonal_board = [
            [0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 1, 1],
            [0, 0, 0, 0, 1, 1, 1],
            [0, 0, 0, 1, 1, 1, 1],
            [0, 0, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1],
        ]

        # Winning Board Setups
        # Each array if consists of two arrays:
        # The first stores win states for '1'
        # The second stores win state for '-1'
        # Note these are not necessarily valid board states
        # for simplicity (random -1 and 1s could be added)
        horizontal_win_boards = [
            [
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [1, 1, 1, 1, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 1, 1, 1, 1],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 1, 1, 1, 1, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
            ],
            [
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [-1, -1, -1, -1, 0, 0, 0],
                ],
                [
                    [0, 0, 0, -1, -1, -1, -1],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, -1, -1, -1, -1, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
            ],
        ]

        vertical_win_boards = [
            [
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [1, 0, 0, 0, 0, 0, 0],
                    [1, 0, 0, 0, 0, 0, 0],
                    [1, 0, 0, 0, 0, 0, 0],
                    [1, 0, 0, 0, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 0, 0, 0, 1],
                    [0, 0, 0, 0, 0, 0, 1],
                    [0, 0, 0, 0, 0, 0, 1],
                    [0, 0, 0, 0, 0, 0, 1],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
            ],
            [
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [-1, 0, 0, 0, 0, 0, 0],
                    [-1, 0, 0, 0, 0, 0, 0],
                    [-1, 0, 0, 0, 0, 0, 0],
                    [-1, 0, 0, 0, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 0, 0, 0, -1],
                    [0, 0, 0, 0, 0, 0, -1],
                    [0, 0, 0, 0, 0, 0, -1],
                    [0, 0, 0, 0, 0, 0, -1],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, -1, 0, 0, 0],
                    [0, 0, 0, -1, 0, 0, 0],
                    [0, 0, 0, -1, 0, 0, 0],
                    [0, 0, 0, -1, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
            ],
        ]

        major_diagonal_win_boards = [
            [
                [
                    [1, 0, 0, 0, 0, 0, 0],
                    [0, 1, 0, 0, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 0, 1, 0, 0],
                    [0, 0, 0, 0, 0, 1, 0],
                    [0, 0, 0, 0, 0, 0, 1],
                ],
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 0, 1, 0, 0],
                    [0, 0, 0, 0, 0, 1, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
            ],
            [
                [
                    [-1, 0, 0, 0, 0, 0, 0],
                    [0, -1, 0, 0, 0, 0, 0],
                    [0, 0, -1, 0, 0, 0, 0],
                    [0, 0, 0, -1, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, -1, 0, 0, 0],
                    [0, 0, 0, 0, -1, 0, 0],
                    [0, 0, 0, 0, 0, -1, 0],
                    [0, 0, 0, 0, 0, 0, -1],
                ],
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, -1, 0, 0, 0, 0],
                    [0, 0, 0, -1, 0, 0, 0],
                    [0, 0, 0, 0, -1, 0, 0],
                    [0, 0, 0, 0, 0, -1, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
            ],
        ]

        minor_diagonal_win_boards = [
            [
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0, 0],
                    [0, 1, 0, 0, 0, 0, 0],
                    [1, 0, 0, 0, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 0, 0, 0, 1],
                    [0, 0, 0, 0, 0, 1, 0],
                    [0, 0, 0, 0, 1, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 1, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0, 0],
                    [0, 1, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
            ],
            [
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, -1, 0, 0, 0],
                    [0, 0, -1, 0, 0, 0, 0],
                    [0, -1, 0, 0, 0, 0, 0],
                    [-1, 0, 0, 0, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 0, 0, 0, -1],
                    [0, 0, 0, 0, 0, -1, 0],
                    [0, 0, 0, 0, -1, 0, 0],
                    [0, 0, 0, -1, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, -1, 0, 0],
                    [0, 0, 0, -1, 0, 0, 0],
                    [0, 0, -1, 0, 0, 0, 0],
                    [0, -1, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ],
            ],
        ]

        # Test Move Validation Logic
        confirm_available_moves([0, 1, 2, 3, 4, 5, 6], [-1, 7], blank_board)
        confirm_available_moves([3], [0, 1, 2, 4, 5, 6], single_column_board)
        confirm_available_moves([0, 1, 2, 3, 4, 5], [6], diagonal_board)

        # Test Available Move Logic
        connect_four_model.update_board(blank_board)
        self.assertEqual(connect_four_model.available_moves(), [0, 1, 2, 3, 4, 5, 6])

        connect_four_model.update_board(single_column_board)
        self.assertEqual(connect_four_model.available_moves(), [3])

        connect_four_model.update_board(full_board)
        self.assertEqual(connect_four_model.available_moves(), [])

        # Test Move Logic
        confirm_move(
            1,
            0,
            blank_board,
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0, 0],
            ],
        )

        confirm_move(
            1,
            1,
            blank_board,
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [-1, 0, 0, 0, 0, 0, 0],
            ],
        )

        confirm_move(
            1,
            0,
            diagonal_board,
            [
                [0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 1, 1],
                [0, 0, 0, 0, 1, 1, 1],
                [0, 0, 0, 1, 1, 1, 1],
                [0, 0, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1, 1, 1],
            ],
        )

        confirm_move(
            2,
            0,
            diagonal_board,
            [
                [0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 1, 1],
                [0, 0, 0, 0, 1, 1, 1],
                [0, 0, 0, 1, 1, 1, 1],
                [0, 1, 1, 1, 1, 1, 1],
                [0, 1, 1, 1, 1, 1, 1],
            ],
        )

        confirm_move(
            3,
            0,
            diagonal_board,
            [
                [0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 1, 1],
                [0, 0, 0, 0, 1, 1, 1],
                [0, 0, 1, 1, 1, 1, 1],
                [0, 0, 1, 1, 1, 1, 1],
                [0, 1, 1, 1, 1, 1, 1],
            ],
        )

        confirm_move(
            4,
            0,
            diagonal_board,
            [
                [0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 1, 1],
                [0, 0, 0, 1, 1, 1, 1],
                [0, 0, 0, 1, 1, 1, 1],
                [0, 0, 1, 1, 1, 1, 1],
                [0, 1, 1, 1, 1, 1, 1],
            ],
        )

        confirm_move(
            5,
            0,
            diagonal_board,
            [
                [0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 1, 1, 1],
                [0, 0, 0, 0, 1, 1, 1],
                [0, 0, 0, 1, 1, 1, 1],
                [0, 0, 1, 1, 1, 1, 1],
                [0, 1, 1, 1, 1, 1, 1],
            ],
        )

        confirm_move(
            6,
            0,
            diagonal_board,
            [
                [0, 0, 0, 0, 0, 1, 1],
                [0, 0, 0, 0, 0, 1, 1],
                [0, 0, 0, 0, 1, 1, 1],
                [0, 0, 0, 1, 1, 1, 1],
                [0, 0, 1, 1, 1, 1, 1],
                [0, 1, 1, 1, 1, 1, 1],
            ],
        )

        # Test Game Over Logic:
        confirm_game_over(blank_board, "")
        confirm_game_over(full_board, "draw")

        # Test Win States:
        confirm_win_states(horizontal_win_boards)
        confirm_win_states(vertical_win_boards)
        confirm_win_states(major_diagonal_win_boards)
        confirm_win_states(minor_diagonal_win_boards)

    def test_more_logic(self) -> None:
        model = ConnectFourModel()
        move = "move 4"
        col = 3  # zero-indexed

        self.assertEqual(model.get_column(col), [0, 0, 0, 0, 0, 0])
        model.make_move(move, player_number=0)
        self.assertEqual(model.get_column(col), [0, 0, 0, 0, 0, 1])
        model.make_move(move, player_number=0)
        self.assertEqual(model.get_column(col), [0, 0, 0, 0, 1, 1])
        model.make_move(move, player_number=1)
        self.assertEqual(model.get_column(col), [0, 0, 0, -1, 1, 1])
        model.make_move(move, player_number=1)
        self.assertEqual(model.get_column(col), [0, 0, -1, -1, 1, 1])
        model.make_move(move, player_number=1)
        self.assertEqual(model.get_column(col), [0, -1, -1, -1, 1, 1])
        model.make_move(move, player_number=0)
        self.assertEqual(model.get_column(col), [1, -1, -1, -1, 1, 1])
        with self.assertRaises(BadMoveError):
            model.make_move(move, player_number=0)

"""
Most of the testing for the actual game are done in test_database

This is only to really verify the output of the chat
"""

from unittest import mock

import zulip_bots.bots.merels.merels
import zulip_bots.test_lib


class TestFollowUpBot(zulip_bots.test_lib.BotTestCase):
    bot_name = "merels"

    def test_no_command(self):
        message = dict(
            content='magic',
            type='stream',
        )

        res = self.get_response(message)

        self.assertEqual(res['content'],
                         'Unknown command. Available commands: create, '
                         'reset, help, put (v,h), take (v,h), move (v,'
                         'h) -> (v,h)')

    def test_help_command(self):
        message = dict(
            content='help',
            type='stream',
        )

        res = self.get_response(message)

        self.assertEqual(res['content'], "Commands:\ncreate: Create a new "
                                         "game if it doesn't exist\nreset: "
                                         "Reset a current game\nput (v,"
                                         "h): Put a man into the grid in "
                                         "phase 1\nmove (v,h) -> (v,"
                                         "h): Moves a man from one point to "
                                         "-> another point\ntake (v,h): Take "
                                         "an opponent's man from the grid in "
                                         "phase 2/3\n\nv: vertical position "
                                         "of grid\nh: horizontal position of "
                                         "grid")

    def test_create_new_game(self):
        message = dict(
            content='create',
            type='stream',
            subject='test'
        )

        with mock.patch.object(zulip_bots.bots.merels.merels.MerelsBot,
                               'compose_room_name',
                               return_value="test"):
            res = self.get_response(message)

        self.assertEqual(res['content'], '''A room has been created in test. Starting game now.
`      0     1     2     3     4     5     6
    0 [ ]---------------[ ]---------------[ ]
       |                 |                 |
    1  |    [ ]---------[ ]---------[ ]    |
       |     |           |           |     |
    2  |     |    [ ]---[ ]---[ ]    |     |
       |     |     |           |     |     |
    3 [ ]---[ ]---[ ]         [ ]---[ ]---[ ]
       |     |     |           |     |     |
    4  |     |    [ ]---[ ]---[ ]    |     |
       |     |           |           |     |
    5  |    [ ]---------[ ]---------[ ]    |
       |                 |                 |
    6 [ ]---------------[ ]---------------[ ]`
Phase 1, X's turn. Take mode: No.
X taken: 0, O taken: 0.\n    ''')

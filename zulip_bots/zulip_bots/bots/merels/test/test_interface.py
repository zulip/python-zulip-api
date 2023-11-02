import unittest

from zulip_bots.bots.merels.libraries import interface


class BoardLayoutTest(unittest.TestCase):
    def test_empty_layout_arrangement(self):
        grid = interface.construct_grid("NNNNNNNNNNNNNNNNNNNNNNNN")
        self.assertEqual(
            interface.graph_grid(grid),
            """`      0     1     2     3     4     5     6
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
    6 [ ]---------------[ ]---------------[ ]`""",
        )

    def test_full_layout_arragement(self):
        grid = interface.construct_grid("NXONXONXONXONXONXONXONXO")
        self.assertEqual(
            interface.graph_grid(grid),
            """`      0     1     2     3     4     5     6
    0 [ ]---------------[X]---------------[O]
       |                 |                 |
    1  |    [ ]---------[X]---------[O]    |
       |     |           |           |     |
    2  |     |    [ ]---[X]---[O]    |     |
       |     |     |           |     |     |
    3 [ ]---[X]---[O]         [ ]---[X]---[O]
       |     |     |           |     |     |
    4  |     |    [ ]---[X]---[O]    |     |
       |     |           |           |     |
    5  |    [ ]---------[X]---------[O]    |
       |                 |                 |
    6 [ ]---------------[X]---------------[O]`""",
        )

    def test_illegal_character_arrangement(self):
        grid = interface.construct_grid("ABCDABCDABCDABCDABCDXXOO")
        self.assertEqual(
            interface.graph_grid(grid),
            """`      0     1     2     3     4     5     6
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
    5  |    [ ]---------[ ]---------[X]    |
       |                 |                 |
    6 [X]---------------[O]---------------[O]`""",
        )


class ParsingTest(unittest.TestCase):
    def test_consistent_parse(self):
        boards = [
            "NNNNOOOOXXXXNNNNOOOOXXXX",
            "NOXNXOXNOXNOXOXOXNOXONON",
            "OOONXNOXNONXONOXNXNNONOX",
            "NNNNNNNNNNNNNNNNNNNNNNNN",
            "OOOOOOOOOOOOOOOOOOOOOOOO",
            "XXXXXXXXXXXXXXXXXXXXXXXX",
        ]

        for board in boards:
            self.assertEqual(
                board,
                interface.construct_board(
                    interface.construct_grid(
                        interface.construct_board(interface.construct_grid(board))
                    )
                ),
            )

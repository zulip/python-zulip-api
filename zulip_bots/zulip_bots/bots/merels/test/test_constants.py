import unittest

from zulip_bots.bots.merels.libraries import constants


class CheckIntegrity(unittest.TestCase):
    def test_grid_layout_integrity(self):
        grid_layout = (
            [0, 0],
            [0, 3],
            [0, 6],
            [1, 1],
            [1, 3],
            [1, 5],
            [2, 2],
            [2, 3],
            [2, 4],
            [3, 0],
            [3, 1],
            [3, 2],
            [3, 4],
            [3, 5],
            [3, 6],
            [4, 2],
            [4, 3],
            [4, 4],
            [5, 1],
            [5, 3],
            [5, 5],
            [6, 0],
            [6, 3],
            [6, 6],
        )

        self.assertEqual(constants.ALLOWED_MOVES, grid_layout, "Incorrect grid layout.")

    def test_relative_hills_integrity(self):
        grid_layout = (
            [0, 0],
            [0, 3],
            [0, 6],
            [1, 1],
            [1, 3],
            [1, 5],
            [2, 2],
            [2, 3],
            [2, 4],
            [3, 0],
            [3, 1],
            [3, 2],
            [3, 4],
            [3, 5],
            [3, 6],
            [4, 2],
            [4, 3],
            [4, 4],
            [5, 1],
            [5, 3],
            [5, 5],
            [6, 0],
            [6, 3],
            [6, 6],
        )

        am = grid_layout

        relative_hills = (
            [am[0], am[1], am[2]],
            [am[3], am[4], am[5]],
            [am[6], am[7], am[8]],
            [am[9], am[10], am[11]],
            [am[12], am[13], am[14]],
            [am[15], am[16], am[17]],
            [am[18], am[19], am[20]],
            [am[21], am[22], am[23]],
            [am[0], am[9], am[21]],
            [am[3], am[10], am[18]],
            [am[6], am[11], am[15]],
            [am[1], am[4], am[7]],
            [am[16], am[19], am[22]],
            [am[8], am[12], am[17]],
            [am[5], am[13], am[20]],
            [am[2], am[14], am[23]],
        )

        self.assertEqual(constants.HILLS, relative_hills, "Incorrect relative hills arrangement")

import unittest

from ..libraries import constants


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

        AM = grid_layout

        relative_hills = (
            [AM[0], AM[1], AM[2]],
            [AM[3], AM[4], AM[5]],
            [AM[6], AM[7], AM[8]],
            [AM[9], AM[10], AM[11]],
            [AM[12], AM[13], AM[14]],
            [AM[15], AM[16], AM[17]],
            [AM[18], AM[19], AM[20]],
            [AM[21], AM[22], AM[23]],
            [AM[0], AM[9], AM[21]],
            [AM[3], AM[10], AM[18]],
            [AM[6], AM[11], AM[15]],
            [AM[1], AM[4], AM[7]],
            [AM[16], AM[19], AM[22]],
            [AM[8], AM[12], AM[17]],
            [AM[5], AM[13], AM[20]],
            [AM[2], AM[14], AM[23]],
        )

        self.assertEqual(constants.HILLS, relative_hills, "Incorrect relative hills arrangement")

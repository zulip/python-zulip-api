"""Provide some constants that are crucial for running the game
"""

# Do NOT scramble these. This is written such that it starts from top left
# to bottom right.
ALLOWED_MOVES = (
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

AM = ALLOWED_MOVES

# Do NOT scramble these, This is written such that it starts from horizontal
#  to vertical, top to bottom, left to right.
HILLS = (
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

OUTER_SQUARE = (
    [0, 0],
    [0, 1],
    [0, 2],
    [0, 3],
    [0, 4],
    [0, 5],
    [0, 6],
    [1, 0],
    [2, 0],
    [3, 0],
    [4, 0],
    [5, 0],
    [6, 0],
    [6, 0],
    [6, 1],
    [6, 2],
    [6, 3],
    [6, 4],
    [6, 5],
    [6, 6],
    [0, 6],
    [1, 6],
    [2, 6],
    [3, 6],
    [4, 6],
    [5, 6],
)

MIDDLE_SQUARE = (
    [1, 1],
    [1, 2],
    [1, 3],
    [1, 4],
    [1, 5],
    [2, 1],
    [3, 1],
    [4, 1],
    [5, 1],
    [5, 1],
    [5, 2],
    [5, 3],
    [5, 4],
    [5, 5],
    [1, 5],
    [2, 5],
    [3, 5],
    [4, 5],
)

INNER_SQUARE = ([2, 2], [2, 3], [2, 4], [3, 2], [3, 4], [4, 2], [4, 3], [4, 4])

EMPTY_BOARD = "NNNNNNNNNNNNNNNNNNNNNNNN"

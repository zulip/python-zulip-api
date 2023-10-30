"""Interface helps the game displaying and maintaining the board. This is
where the grid can get translated into a board, which is easier to manage
in the database, and board translated to grid, which is easier to manage in
the mechanics.

The display heavily depends on the availability of monospaced font. This is
why the graph_grid() is wrapped in `` (it is expected for the user to
provide a Markdown support)
"""

from . import constants


def draw_grid(grid):
    """Draws a board from a grid

    :param grid: a 2-dimensional 7x7 list
    :return: None
    """
    print(graph_grid(grid))


def graph_grid(grid):
    """Creates a nice grid display, something like this:

       0     1     2     3     4     5     6
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
    6 [ ]---------------[ ]---------------[ ]

    :param grid: a 2-dimensional 7x7 list.
    :return: A nicer display of the grid
    """

    return """`      0     1     2     3     4     5     6
    0 [{}]---------------[{}]---------------[{}]
       |                 |                 |
    1  |    [{}]---------[{}]---------[{}]    |
       |     |           |           |     |
    2  |     |    [{}]---[{}]---[{}]    |     |
       |     |     |           |     |     |
    3 [{}]---[{}]---[{}]         [{}]---[{}]---[{}]
       |     |     |           |     |     |
    4  |     |    [{}]---[{}]---[{}]    |     |
       |     |           |           |     |
    5  |    [{}]---------[{}]---------[{}]    |
       |                 |                 |
    6 [{}]---------------[{}]---------------[{}]`""".format(
        grid[0][0],
        grid[0][3],
        grid[0][6],
        grid[1][1],
        grid[1][3],
        grid[1][5],
        grid[2][2],
        grid[2][3],
        grid[2][4],
        grid[3][0],
        grid[3][1],
        grid[3][2],
        grid[3][4],
        grid[3][5],
        grid[3][6],
        grid[4][2],
        grid[4][3],
        grid[4][4],
        grid[5][1],
        grid[5][3],
        grid[5][5],
        grid[6][0],
        grid[6][3],
        grid[6][6],
    )


def construct_grid(board):
    """Constructs the original grid from the database

    :param board: A compact representation of the grid (example:
    "NONXONXONXONXONNOXNXNNOX")

    :return: A grid
    """

    grid = [[" " for _ in range(7)] for _ in range(7)]

    for k, cell in enumerate(board):
        if cell in ("O", "X"):
            grid[constants.ALLOWED_MOVES[k][0]][constants.ALLOWED_MOVES[k][1]] = cell

    return grid


def construct_board(grid):
    """Constructs a board from a grid

    :param grid: A 2-dimensional 7x7 list

    :return: A board. Board is a compact representation of the grid
    """

    board = ""

    for cell_location in constants.ALLOWED_MOVES:
        cell_content = grid[cell_location[0]][cell_location[1]]
        if cell_content in ("X", "O"):
            board += cell_content
        else:
            board += "N"

    return board

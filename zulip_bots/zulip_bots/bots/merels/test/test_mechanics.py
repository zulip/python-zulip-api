import unittest

from zulip_bots.bots.merels.libraries import database, game_data, interface, mechanics
from zulip_bots.simple_lib import SimpleStorage


class GridTest(unittest.TestCase):
    def test_out_of_grid(self):
        points = [[v, h] for h in range(7) for v in range(7)]
        expected_outcomes = [
            True,
            False,
            False,
            True,
            False,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
            False,
            False,
            True,
            True,
            True,
            False,
            False,
            True,
            True,
            True,
            False,
            True,
            True,
            True,
            False,
            False,
            True,
            True,
            True,
            False,
            False,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False,
            False,
            True,
            False,
            False,
            True,
        ]

        test_outcomes = [mechanics.is_in_grid(point[0], point[1]) for point in points]

        self.assertListEqual(test_outcomes, expected_outcomes)

    def test_jump_and_grids(self):
        points = [
            [0, 0, 1, 1],
            [1, 1, 2, 2],
            [2, 2, 3, 3],
            [0, 0, 0, 2],
            [0, 0, 2, 2],
            [6, 6, 5, 4],
        ]
        expected_outcomes = [True, True, True, True, True, True]

        test_outcomes = [
            mechanics.is_jump(point[0], point[1], point[2], point[3]) for point in points
        ]

        self.assertListEqual(test_outcomes, expected_outcomes)

    def test_jump_special_cases(self):
        points = [
            [0, 0, 0, 3],
            [0, 0, 3, 0],
            [6, 0, 6, 3],
            [4, 2, 6, 2],
            [4, 3, 3, 4],
            [4, 3, 2, 2],
            [0, 0, 0, 6],
            [0, 0, 1, 1],
            [0, 0, 2, 2],
            [3, 0, 3, 1],
            [3, 0, 3, 2],
            [3, 1, 3, 0],
            [3, 1, 3, 2],
        ]

        expected_outcomes = [
            False,
            False,
            False,
            True,
            True,
            True,
            True,
            True,
            True,
            False,
            True,
            False,
            False,
        ]

        test_outcomes = [
            mechanics.is_jump(point[0], point[1], point[2], point[3]) for point in points
        ]

        self.assertListEqual(test_outcomes, expected_outcomes)

    def test_not_populated_move(self):
        grid = interface.construct_grid("XXXNNNOOOXXXNNNOOOXXXNNN")

        moves = [[0, 0, 1, 1], [0, 3, 1, 3], [5, 1, 5, 3], [0, 0, 0, 3], [0, 0, 3, 0]]

        expected_outcomes = [True, True, False, False, False]

        test_outcomes = [mechanics.is_empty(move[2], move[3], grid) for move in moves]

        self.assertListEqual(test_outcomes, expected_outcomes)

    def test_legal_move(self):
        grid = interface.construct_grid("XXXNNNOOONNNNNNOOONNNNNN")

        presets = [
            [0, 0, 0, 3, "X", 1],
            [0, 0, 0, 6, "X", 2],
            [0, 0, 3, 6, "X", 3],
            [0, 0, 2, 2, "X", 3],
        ]

        expected_outcomes = [False, False, True, False]

        test_outcomes = [
            mechanics.is_legal_move(
                preset[0], preset[1], preset[2], preset[3], preset[4], preset[5], grid
            )
            for preset in presets
        ]

        self.assertListEqual(test_outcomes, expected_outcomes)

    def test_legal_put(self):
        grid = interface.construct_grid("XXXNNNOOOXXXNNNOOOXXXNNN")

        presets = [[0, 0, 1], [0, 3, 2], [0, 6, 3], [1, 1, 2], [1, 3, 1], [1, 6, 1], [1, 5, 1]]

        expected_outcomes = [False, False, False, False, True, False, True]

        test_outcomes = [
            mechanics.is_legal_put(preset[0], preset[1], grid, preset[2]) for preset in presets
        ]

        self.assertListEqual(test_outcomes, expected_outcomes)

    def test_legal_take(self):
        grid = interface.construct_grid("XXXNNNOOOXXXNNNOOOXXXNNN")

        presets = [
            [0, 0, "X", 1],
            [0, 1, "X", 1],
            [0, 0, "O", 1],
            [0, 0, "O", 0],
            [0, 1, "O", 1],
            [2, 2, "X", 1],
            [2, 3, "X", 1],
            [2, 4, "O", 1],
        ]

        expected_outcomes = [False, False, True, False, False, True, True, False]

        test_outcomes = [
            mechanics.is_legal_take(preset[0], preset[1], preset[2], grid, preset[3])
            for preset in presets
        ]

        self.assertListEqual(test_outcomes, expected_outcomes)

    def test_own_piece(self):
        grid = interface.construct_grid("XXXNNNOOOXXXNNNOOOXXXNNN")

        presets = [[0, 0, "X"], [0, 0, "O"], [0, 6, "X"], [0, 6, "O"], [1, 1, "X"], [1, 1, "O"]]

        expected_outcomes = [True, False, True, False, False, False]

        test_outcomes = [
            mechanics.is_own_piece(preset[0], preset[1], preset[2], grid) for preset in presets
        ]

        self.assertListEqual(test_outcomes, expected_outcomes)

    def test_can_make_any_move(self):
        grid = interface.construct_grid("NONNNNNNNNNNNNNNNNNNNNXN")

        self.assertEqual(mechanics.check_moves("O", grid), True)
        self.assertEqual(mechanics.check_moves("X", grid), True)

        grid = interface.construct_grid("XXXXXXOXXXXXXXXXXXXXXXNX")

        self.assertEqual(mechanics.check_moves("O", grid), False)
        self.assertEqual(mechanics.check_moves("X", grid), True)

        grid = interface.construct_grid("NXNNNNNNNNNNNNNNNNNNNNNN")

        self.assertEqual(mechanics.check_moves("O", grid), False)
        self.assertEqual(mechanics.check_moves("X", grid), True)


class HillsTest(unittest.TestCase):
    def test_unchanged_hills(self):
        grid = interface.construct_grid("XXXNNNOOOXXXXNNOOOXXXNNN")

        hills_uid = "02356"

        mechanics.move_man_legal(3, 4, 3, 5, grid)

        updated_hills_uid = mechanics.get_hills_numbers(grid)

        self.assertEqual(updated_hills_uid, hills_uid)

    def test_no_diagonal_hills(self):
        grid = interface.construct_grid("XXXNNXOONXXXXNNOOOXXXNNN")

        hills_uid = "0356"

        mechanics.move_man_legal(3, 4, 2, 4, grid)

        updated_hills_uid = mechanics.get_hills_numbers(grid)

        self.assertEqual(updated_hills_uid, hills_uid)


class PhaseTest(unittest.TestCase):
    def test_new_game_phase(self):
        storage = SimpleStorage()
        topic_name = "test"
        merels = database.MerelsStorage(topic_name, storage)
        merels.update_game(topic_name, "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)

        res = game_data.GameData(merels.get_game_data("test"))
        self.assertEqual(res.get_phase(), 1)

        merels.update_game(res.topic_name, "O", 5, 4, "XXXXNNNOOOOONNNNNNNNNNNN", "03", 0)
        res = game_data.GameData(merels.get_game_data("test"))
        self.assertEqual(res.board, "XXXXNNNOOOOONNNNNNNNNNNN")
        self.assertEqual(res.get_phase(), 2)

        merels.update_game(res.topic_name, "X", 6, 4, "XXXNNNNOOOOONNNNNNNNNNNN", "03", 0)
        res = game_data.GameData(merels.get_game_data("test"))
        self.assertEqual(res.board, "XXXNNNNOOOOONNNNNNNNNNNN")
        self.assertEqual(res.get_phase(), 3)

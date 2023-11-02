import unittest

from zulip_bots.bots.merels.libraries import database, game
from zulip_bots.game_handler import BadMoveError
from zulip_bots.simple_lib import SimpleStorage


class GameTest(unittest.TestCase):
    def setUp(self):
        self.storage = SimpleStorage()
        self.topic_name = "test"

    def test_command_when_no_game_created_output(self):
        with self.assertRaises(TypeError) as warning:
            resp, move = game.beat("put 0,0", self.topic_name, self.storage)
            self.assertTrue("NoneType" in str(warning))

    def test_put_piece_output(self):
        merels = database.MerelsStorage(self.topic_name, self.storage)
        # All new games start with updating the game as follows
        merels.update_game(self.topic_name, "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        resp, move = game.beat("put 0,0", self.topic_name, self.storage)
        self.assertTrue("Put a man" in resp)

    def test_not_possible_put_piece_output(self):
        merels = database.MerelsStorage(self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        with self.assertRaises(BadMoveError) as warning:
            game.beat("put 0,1", self.topic_name, self.storage)
            self.assertTrue("Failed" in str(warning))

    def test_take_before_put_output(self):
        merels = database.MerelsStorage(self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        merels.update_game(self.topic_name, "X", 0, 0, "XXXNNNOOOXXXNNNOOOXXXNNN", "", 1)
        with self.assertRaises(BadMoveError) as warning:
            game.beat("put 1,1", self.topic_name, self.storage)
            self.assertTrue("Take is required" in str(warning))

    def test_move_piece_output(self):
        merels = database.MerelsStorage(self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        merels.update_game(self.topic_name, "X", 0, 0, "XXXNNNOOOXXXNNNOOOXXXOOO", "", 0)
        resp, _ = game.beat("move 0,3 1,3", self.topic_name, self.storage)
        self.assertTrue("Moved a man" in resp)

    def test_not_possible_move_piece_output(self):
        merels = database.MerelsStorage(self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        merels.update_game(self.topic_name, "X", 0, 0, "XXXNNNOOOXXXNNNOOOXXXOOO", "", 0)
        with self.assertRaises(BadMoveError) as warning:
            game.beat("move 0,3 1,2", self.topic_name, self.storage)
            self.assertTrue("Failed" in str(warning))

    def test_cannot_make_any_move_output(self):
        merels = database.MerelsStorage(self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        merels.update_game(self.topic_name, "X", 3, 4, "OOXOXNOXNNOXNNNNNNXNNXNN", "", 0)
        _, move = game.beat("move 6,0 3,0", self.topic_name, self.storage)
        self.assertTrue("Switching" in move)

    def test_take_before_move_output(self):
        merels = database.MerelsStorage(self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        merels.update_game(self.topic_name, "X", 6, 6, "XXXNNNOOONNNNNNNNNNNNNNN", "", 1)
        with self.assertRaises(BadMoveError) as warning:
            game.beat("move 0,1 1,3", self.topic_name, self.storage)
            self.assertTrue("Take is required" in str(warning))

    def test_unknown_command(self):
        merels = database.MerelsStorage(self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        merels.update_game(self.topic_name, "X", 6, 6, "XXXNNNOOONNNNNNNNNNNNNNN", "", 1)
        with self.assertRaises(BadMoveError) as warning:
            game.beat("magic 2,2", self.topic_name, self.storage)
            self.assertTrue("Unknown command" in str(warning))

    def test_take_piece_output(self):
        merels = database.MerelsStorage(self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        merels.update_game(self.topic_name, "X", 0, 0, "XXXNNNOOOXXXNNNOOOXXXOOO", "", 1)
        resp, move = game.beat("take 2,2", self.topic_name, self.storage)
        self.assertTrue("Taken a man" in resp)

    def test_not_possible_take_piece_output(self):
        merels = database.MerelsStorage(self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        merels.update_game(self.topic_name, "X", 6, 6, "XXXNNNOOOXXXNNNOOOXXXOOO", "", 0)
        with self.assertRaises(BadMoveError) as warning:
            game.beat("take 2,2", self.topic_name, self.storage)
            self.assertTrue("Taking is not possible" in str(warning))

    def test_win_output(self):
        merels = database.MerelsStorage(self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        merels.update_game(self.topic_name, "X", 6, 6, "XXXNNNOOONNNNNNNNNNNNNNN", "", 1)
        resp, _ = game.beat("take 2,2", self.topic_name, self.storage)
        self.assertTrue("wins the game!" in resp)

import unittest

from libraries import game
from libraries import database

from zulip_bots.simple_lib import SimpleStorage


class GameTest(unittest.TestCase):
    def setUp(self):
        self.storage = SimpleStorage()
        self.topic_name = "test"

    def test_reset_game_output(self):
        game.beat("create", self.topic_name, self.storage)
        self.assertTrue("reset" in game.beat("reset", self.topic_name,
                                             self.storage))

    def test_reset_no_game_output(self):
        self.assertTrue("No game created yet" in game.beat("reset",
                                                           self.topic_name,
                                                           self.storage))

    def test_command_when_no_game_created_output(self):
        self.assertTrue("cannot do any of the game commands" in game.beat(
            "put 0,0", self.topic_name, self.storage))

    def test_put_piece_output(self):
        game.beat("create", self.topic_name, self.storage)
        self.assertTrue("Put a man" in game.beat("put 0,0", self.topic_name,
                                                 self.storage))

    def test_not_possible_put_piece_output(self):
        game.beat("create", self.topic_name, self.storage)
        self.assertTrue("Failed" in game.beat("put 0,1", self.topic_name,
                                              self.storage))

    def test_take_before_put_output(self):
        merels = database.MerelsStorage(self.storage)
        game.beat("create", self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0,
                           "XXXNNNOOOXXXNNNOOOXXXNNN", "", 1)
        self.assertTrue("Take is required", game.beat("put 1,1",
                                                      self.topic_name,
                                                      self.storage))

    def test_move_piece_output(self):
        merels = database.MerelsStorage(self.storage)
        game.beat("create", self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0,
                           "XXXNNNOOOXXXNNNOOOXXXOOO", "", 0)
        self.assertTrue("Moved a man" in game.beat("move 0,3 1,3",
                                                   self.topic_name,
                                                   self.storage))

    def test_not_possible_move_piece_output(self):
        merels = database.MerelsStorage(self.storage)
        game.beat("create", self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0,
                           "XXXNNNOOOXXXNNNOOOXXXOOO", "", 0)
        self.assertTrue("Failed" in game.beat("move 0,3 1,2",
                                              self.topic_name,
                                              self.storage))

    def test_cannot_make_any_move_output(self):
        merels = database.MerelsStorage(self.storage)
        game.beat("create", self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 3, 4,
                           "OOXOXNOXNNOXNNNNNNXNNXNN", "", 0)
        self.assertTrue("Switching" in game.beat("move 6,0 3,0",
                                                 self.topic_name,
                                                 self.storage))

    def test_take_before_move_output(self):
        merels = database.MerelsStorage(self.storage)
        game.beat("create", self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 6, 6,
                           "XXXNNNOOONNNNNNNNNNNNNNN", "", 1)
        self.assertTrue("Take is required", game.beat("move 0,1 1,3",
                                                      self.topic_name,
                                                      self.storage))

    def test_unknown_command(self):
        merels = database.MerelsStorage(self.storage)
        game.beat("create", self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 6, 6,
                           "XXXNNNOOONNNNNNNNNNNNNNN", "", 1)
        self.assertTrue("Unknown command", game.beat("magic 2,2",
                                                     self.topic_name,
                                                     self.storage))

    def test_take_piece_output(self):
        merels = database.MerelsStorage(self.storage)
        game.beat("create", self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 0, 0,
                           "XXXNNNOOOXXXNNNOOOXXXOOO", "", 1)
        self.assertTrue("Taken a man" in game.beat("take 2,2",
                                                   self.topic_name,
                                                   self.storage))

    def test_not_possible_take_piece_output(self):
        merels = database.MerelsStorage(self.storage)
        game.beat("create", self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 6, 6,
                           "XXXNNNOOOXXXNNNOOOXXXOOO", "", 0)
        self.assertTrue("Taking is not possible" in game.beat("take 2,2",
                                                              self.topic_name,
                                                              self.storage))

    def test_win_output(self):
        merels = database.MerelsStorage(self.storage)
        game.beat("create", self.topic_name, self.storage)
        merels.update_game(self.topic_name, "X", 6, 6,
                           "XXXNNNOOONNNNNNNNNNNNNNN", "", 1)
        self.assertTrue("wins the game!", game.beat("take 2,2",
                                                    self.topic_name,
                                                    self.storage))

import unittest

from libraries import database
from libraries import game_data
from zulip_bots.simple_lib import SimpleStorage


class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.storage = SimpleStorage()
        self.merels = database.MerelsStorage(self.storage)

    def test_create_duplicate_game(self):
        self.merels.create_new_game("test")

        self.assertEqual(self.merels.create_new_game("test"), False)

    def test_obtain_gamedata(self):
        self.merels.create_new_game("test")

        res = self.merels.get_game_data("test")
        self.assertTupleEqual(res, (
            'test', 'X', 0, 0, 'NNNNNNNNNNNNNNNNNNNNNNNN', "", 0))
        self.assertEqual(len(res), 7)

    def test_obtain_nonexisting_gamedata(self):
        res = self.merels.get_game_data("test")

        self.assertEqual(res, None)

    def test_game_session(self):
        self.merels.create_new_game("test")

        self.merels.update_game("test", "O", 5, 4, "XXXXOOOOONNNNNNNNNNNNNNN",
                                "",
                                0)

        self.merels.create_new_game("test2")

        self.assertTrue(self.storage.contains("test"), self.storage.contains(
            "test2"))

        self.assertEqual(
            game_data.GameData(self.merels.get_game_data("test")).board,
            "XXXXOOOOONNNNNNNNNNNNNNN")

    def test_no_duplicates(self):
        self.merels.create_new_game("test")
        self.merels.update_game("test", "X", 0, 0, "XXXNNNOOOXXXNNNOOOXXXNNN",
                                "", 1)
        self.merels.create_new_game("test")
        self.merels.create_new_game("test")
        self.merels.create_new_game("test")
        self.merels.create_new_game("test")
        self.merels.create_new_game("test")
        self.merels.create_new_game("test")
        self.merels.create_new_game("test")

        self.assertEqual(game_data.GameData(self.merels.get_game_data(
            "test")).board, "XXXNNNOOOXXXNNNOOOXXXNNN")

    def test_remove_game(self):
        self.merels.create_new_game("test")
        self.merels.remove_game("test")

        self.assertTrue(self.merels.create_new_game("test"))

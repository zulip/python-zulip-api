from zulip_bots.bots.merels.libraries import database, game_data
from zulip_bots.simple_lib import SimpleStorage
from zulip_bots.test_lib import BotTestCase, DefaultTests


class DatabaseTest(BotTestCase, DefaultTests):
    bot_name = "merels"

    def setUp(self):
        self.storage = SimpleStorage()
        self.merels = database.MerelsStorage("", self.storage)

    def test_obtain_gamedata(self):
        self.merels.update_game("topic1", "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        res = self.merels.get_game_data("topic1")
        self.assertTupleEqual(res, ("topic1", "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0))
        self.assertEqual(len(res), 7)

    def test_obtain_nonexisting_gamedata(self):
        res = self.merels.get_game_data("NoGame")
        self.assertEqual(res, None)

    def test_game_session(self):
        self.merels.update_game("topic1", "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        self.merels.update_game("topic2", "O", 5, 4, "XXXXOOOOONNNNNNNNNNNNNNN", "", 0)
        self.assertTrue(self.storage.contains("topic1"), self.storage.contains("topic2"))
        topic2_board = game_data.GameData(self.merels.get_game_data("topic2"))
        self.assertEqual(topic2_board.board, "XXXXOOOOONNNNNNNNNNNNNNN")

    def test_remove_game(self):
        self.merels.update_game("topic1", "X", 0, 0, "NNNNNNNNNNNNNNNNNNNNNNNN", "", 0)
        self.merels.remove_game("topic1")
        self.assertEqual(self.merels.get_game_data("topic1"), None)

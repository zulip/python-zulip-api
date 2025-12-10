from typing import Dict

from typing_extensions import override

from zulip_bots.test_lib import BotTestCase, DefaultTests

from .libraries.constants import EMPTY_BOARD


class TestMerelsBot(BotTestCase, DefaultTests):
    bot_name = "merels"

    def test_no_command(self) -> None:
        # Sanity: out-of-game message for random content.
        message = dict(
            content="magic", type="stream", sender_email="boo@email.com", sender_full_name="boo"
        )
        res = self.get_response(message)
        self.assertEqual(
            res["content"], "You are not in a game at the moment. Type `help` for help."
        )

    def test_parse_board_identity_empty_board(self) -> None:
        # parse_board is identity for Merels; verify with the canonical empty board.
        bot, _ = self._get_handlers()
        self.assertEqual(bot.game_message_handler.parse_board(EMPTY_BOARD), EMPTY_BOARD)


class TestMerelsAdapter(BotTestCase, DefaultTests):
    """
    Adapter-focused tests mirroring connect_four, kept in this file to
    keep Merels tests cohesive. Assert on stable fragments to avoid brittle
    exact-string matches.
    """

    bot_name = "merels"

    @override
    def make_request_message(
        self, content: str, user: str = "foo@example.com", user_name: str = "foo"
    ) -> Dict[str, str]:
        # Provide stream metadata; GameAdapter reads message["type"], topic, etc.
        return {
            "sender_email": user,
            "sender_full_name": user_name,
            "content": content,
            "type": "stream",
            "display_recipient": "general",
            "subject": "merels-test-topic",
        }

    def test_help_is_merels_help(self) -> None:
        bot, bot_handler = self._get_handlers()

        bot_handler.reset_transcript()
        bot.handle_message(self.make_request_message("help"), bot_handler)

        responses = [m for (_method, m) in bot_handler.transcript]
        self.assertTrue(responses, "No bot response to 'help'")
        help_text = responses[0]["content"]

        # Stable fragments; resilient to copy tweaks.
        self.assertIn("Merels Bot Help", help_text)
        self.assertIn("start game", help_text)
        self.assertIn("play game", help_text)
        self.assertIn("quit", help_text)
        self.assertIn("rules", help_text)
        # Present today; OK if dropped in future wording changes.
        self.assertIn("leaderboard", help_text)
        self.assertIn("cancel game", help_text)

    def test_start_game_emits_invite(self) -> None:
        bot, bot_handler = self._get_handlers()
        bot_handler.reset_transcript()

        bot.handle_message(
            self.make_request_message("start game", user="foo@example.com", user_name="foo"),
            bot_handler,
        )

        contents = [m["content"] for (_method, m) in bot_handler.transcript]
        self.assertTrue(contents, "No bot reply recorded for 'start game'")
        first = contents[0]
        self.assertIn("wants to play", first)
        self.assertIn("Merels", first)
        self.assertIn("join", first)

    def test_join_starts_game_emits_start_message(self) -> None:
        bot, bot_handler = self._get_handlers()
        expected_fragment = bot.game_message_handler.game_start_message()

        bot_handler.reset_transcript()
        bot.handle_message(
            self.make_request_message("start game", "foo@example.com", "foo"), bot_handler
        )
        bot.handle_message(self.make_request_message("join", "bar@example.com", "bar"), bot_handler)

        contents = [m["content"] for (_method, m) in bot_handler.transcript]
        self.assertTrue(
            any(expected_fragment in c for c in contents),
            "Merels start message not found after 'join'",
        )

    def test_message_handler_helpers(self) -> None:
        bot, _ = self._get_handlers()

        # parse_board returns the given board representation.
        self.assertEqual(
            bot.game_message_handler.parse_board("sample_board_repr"), "sample_board_repr"
        )

        # Token color is one of the two known emoji.
        self.assertIn(
            bot.game_message_handler.get_player_color(0),
            (":o_button:", ":cross_mark_button:"),
        )
        self.assertIn(
            bot.game_message_handler.get_player_color(1),
            (":o_button:", ":cross_mark_button:"),
        )

        # Basic move alert format.
        self.assertEqual(
            bot.game_message_handler.alert_move_message("foo", "move 1,1"),
            "foo :move 1,1",
        )

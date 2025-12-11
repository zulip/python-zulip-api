from typing import Dict

from typing_extensions import override

from zulip_bots.test_lib import BotTestCase, DefaultTests

from .libraries.constants import EMPTY_BOARD


class TestMerelsBot(BotTestCase, DefaultTests):
    bot_name = "merels"

    def test_no_command(self) -> None:
        # Out-of-game message for arbitrary input.
        message = dict(
            content="magic", type="stream", sender_email="boo@email.com", sender_full_name="boo"
        )
        res = self.get_response(message)
        self.assertEqual(
            res["content"], "You are not in a game at the moment. Type `help` for help."
        )

    def test_parse_board_identity_empty_board(self) -> None:
        # Merels parse_board is identity; verify with the canonical empty board.
        bot, _ = self._get_handlers()
        self.assertEqual(bot.game_message_handler.parse_board(EMPTY_BOARD), EMPTY_BOARD)


class GameAdapterTestLib:
    """Small helpers for driving GameAdapter-based bots in tests."""

    def send(
        self,
        bot,
        bot_handler,
        content: str,
        *,
        user: str = "foo@example.com",
        user_name: str = "foo",
    ) -> None:
        bot.handle_message(
            self.make_request_message(content, user=user, user_name=user_name),
            bot_handler,
        )

    def replies(self, bot_handler):
        # Return the bot message 'content' fields from the transcript.
        return [m["content"] for (_method, m) in bot_handler.transcript]

    def send_and_collect(
        self,
        bot,
        bot_handler,
        content: str,
        *,
        user: str = "foo@example.com",
        user_name: str = "foo",
    ):
        bot_handler.reset_transcript()
        self.send(bot, bot_handler, content, user=user, user_name=user_name)
        return self.replies(bot_handler)


# Note: Merels has no vs-computer mode (in merels.py, supports_computer=False).
# If computer mode is added in the future, add adapter-level tests here.


class TestMerelsAdapter(BotTestCase, DefaultTests, GameAdapterTestLib):
    """Adapter-focused tests (mirrors connect_four); use stable fragment assertions."""

    bot_name = "merels"

    @override
    def make_request_message(
        self, content: str, user: str = "foo@example.com", user_name: str = "foo"
    ) -> Dict[str, str]:
        # Provide stream metadata consumed by GameAdapter.
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

        # Assert on stable fragments to avoid brittle exact matches.
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

        # Identity parse_board.
        self.assertEqual(
            bot.game_message_handler.parse_board("sample_board_repr"), "sample_board_repr"
        )

        # Token color in allowed set.
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

    def test_move_after_join_invokes_make_move_and_replies(self) -> None:
        """
        After start/join, Merels begins in placement (Phase 1). Use 'put v,h'
        and assert the adapter emits an acknowledgement. Try both players to
        avoid assuming turn order.
        """
        bot, bot_handler = self._get_handlers()

        # Start 2P game.
        _ = self.send_and_collect(
            bot, bot_handler, "start game", user="foo@example.com", user_name="foo"
        )
        _ = self.send_and_collect(bot, bot_handler, "join", user="bar@example.com", user_name="bar")

        # Stable oracles from the handler's formatter.
        ack_foo = bot.game_message_handler.alert_move_message("foo", "put 1,1")
        ack_bar = bot.game_message_handler.alert_move_message("bar", "put 1,1")

        # Try current player first (unknown), then the other.
        contents_foo = self.send_and_collect(
            bot, bot_handler, "put 1,1", user="foo@example.com", user_name="foo"
        )
        joined = " ".join(contents_foo)

        if (ack_foo not in joined) and (ack_bar not in joined) and (":put 1,1" not in joined):
            contents_bar = self.send_and_collect(
                bot, bot_handler, "put 1,1", user="bar@example.com", user_name="bar"
            )
            joined += " " + " ".join(contents_bar)

        # Assert the adapter produced a placement acknowledgement.
        self.assertTrue(
            any(h in joined for h in (":put 1,1", ack_foo, ack_bar)),
            f"No placement acknowledgement found in: {joined}",
        )

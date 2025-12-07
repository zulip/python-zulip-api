from typing import Dict

from typing_extensions import override

from zulip_bots.test_lib import BotTestCase, DefaultTests


class TestMerelsAdapter(BotTestCase, DefaultTests):
    bot_name = "merels"

    @override
    def make_request_message(
        self, content: str, user: str = "foo@example.com", user_name: str = "foo"
    ) -> Dict[str, str]:
        # Include stream context; the adapter checks message["type"] and topic.
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

        # Assert on stable fragments; avoid brittle exact-match checks.
        self.assertIn("Merels Bot Help", help_text)
        self.assertIn("start game", help_text)
        self.assertIn("play game", help_text)
        self.assertIn("quit", help_text)
        self.assertIn("rules", help_text)
        # Present today; OK to drop later if wording changes.
        self.assertIn("leaderboard", help_text)
        self.assertIn("cancel game", help_text)

    def test_start_game_emits_invite(self) -> None:
        bot, bot_handler = self._get_handlers()
        bot_handler.reset_transcript()

        bot.handle_message(
            self.make_request_message("start game", user="foo@example.com", user_name="foo"),
            bot_handler,
        )

        responses = [m["content"] for (_method, m) in bot_handler.transcript]
        self.assertTrue(responses, "No bot reply recorded for 'start game'")
        first = responses[0]
        self.assertIn("wants to play", first)
        self.assertIn("Merels", first)
        self.assertIn("join", first)

    def test_join_starts_game_emits_start_message(self) -> None:
        bot, bot_handler = self._get_handlers()
        expected_fragment = bot.game_message_handler.game_start_message()

        bot_handler.reset_transcript()
        bot.handle_message(
            self.make_request_message("start game", user="foo@example.com", user_name="foo"),
            bot_handler,
        )
        bot.handle_message(
            self.make_request_message("join", user="bar@example.com", user_name="bar"),
            bot_handler,
        )

        contents = [m["content"] for (_method, m) in bot_handler.transcript]
        self.assertTrue(
            any(expected_fragment in c for c in contents),
            "Merels start message not found after 'join'",
        )

    def test_message_handler_helpers(self) -> None:
        bot, _ = self._get_handlers()

        # parse_board is identity for Merels.
        self.assertEqual(
            bot.game_message_handler.parse_board("sample_board_repr"), "sample_board_repr"
        )

        # Token color is one of the known emoji.
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

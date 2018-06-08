from zulip_bots.test_lib import BotTestCase, DefaultTests

class TestHelpBot(BotTestCase, DefaultTests):
    bot_name = "helloworld"  # type: str

    def test_bot(self) -> None:
        dialog = [
            ('', 'beep boop'),
            ('help', 'beep boop'),
            ('foo', 'beep boop'),
        ]

        self.verify_dialog(dialog)

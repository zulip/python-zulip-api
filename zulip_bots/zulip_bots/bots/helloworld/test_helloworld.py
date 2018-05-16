from zulip_bots.test_lib import BotTestCase

class TestHelpBot(BotTestCase):
    bot_name = "helloworld"  # type: str

    def test_bot(self) -> None:
        dialog = [
            ('', 'beep boop'),
            ('help', 'beep boop'),
            ('foo', 'beep boop'),
        ]

        self.verify_dialog(dialog)

    def test_bot_silence(self) -> None:
        self.verify_no_reply('silence')

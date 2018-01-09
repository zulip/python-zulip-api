from zulip_bots.test_lib import BotTestCase

class TestMonkeyBot(BotTestCase):
    bot_name = "monkeybot"  # type: str

    def test_bot(self) -> None:
        dialog = [
            ('', 'Invalid syntax m8'),
            ('help', 'Invalid syntax m8'),
            ('http://google.com/', 'Site http://google.com/ exists'),
        ]

        self.verify_dialog(dialog)

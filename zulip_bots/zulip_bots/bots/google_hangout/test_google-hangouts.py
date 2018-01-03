from zulip_bots.test_lib import BotTestCase

class TestHelpBot(BotTestCase):
    bot_name = "google-hangouts"  # type: str

    def test_bot(self) -> None:
        dialog = [
            ('', 'https://hangouts.google.com/'),
            ('help', 'https://hangouts.google.com/'),
            ('foo', 'https://hangouts.google.com/'),
        ]

        self.verify_dialog(dialog)

from zulip_bots.test_lib import BotTestCase

class AIBot(BotTestCase):
    bot_name = "ai_bot"  # type: str

    def test_bot(self) -> None:
        dialog = [
            ('', 'Please enter your message after @mention-bot to chat with AI Bot'),
            ('verify', '```AI Bot says: ```Bot is working fine :-.')
        ]

        self.verify_dialog(dialog)

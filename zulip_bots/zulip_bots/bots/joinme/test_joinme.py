from zulip_bots.test_lib import BotTestCase

class TestHelpBot(BotTestCase):
    bot_name = "joinme"  # type: str

    def test_expired(self) -> None:
        a = 'https://developer.join.me/io-docs/oauth2callback?code=ef4jugsm8yuz2cv5z5sgvvx3&state=ZISSHUDBUNIq'
        b = 'The session has expired. Please start again by @Joinme bot.'
        self.verify_reply(a,b)

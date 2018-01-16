from zulip_bots.test_lib import BotTestCase

class TestHelpBot(BotTestCase):
    bot_name = "joinme"  # type: str

    def test_expired(self) -> None:
        a = 'https://developer.join.me/io-docs/oauth2callback?code=ef4jugsm8yuz2cv5z5sgvvx3&state=ZISSHUDBUNIq'
        b = 'The session has expired. Please start again by @Joinme bot.'
        self.verify_reply(a, b)

    def test_login(self) -> None:
        bot_response = "Please click the link below to log in and authorise " \
            "Joinme:\n None \nAnd please copy and send the url shown " \
            "in browser after clicking accept. Don't forget to @ me!"
        with self.mock_http_conversation('test_login'):
            self.verify_reply('', bot_response)

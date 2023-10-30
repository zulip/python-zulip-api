from unittest.mock import patch

from requests.exceptions import ConnectionError

from zulip_bots.test_lib import BotTestCase, DefaultTests, StubBotHandler

help_text = """
Google translate bot
Please format your message like:
`@-mention "<text_to_translate>" <target-language> <source-language(optional)>`
Visit [here](https://cloud.google.com/translate/docs/languages) for all languages
"""


class TestGoogleTranslateBot(BotTestCase, DefaultTests):
    bot_name = "google_translate"

    def _test(self, message, response, http_config_fixture, http_fixture=None):
        with self.mock_config_info({"key": "abcdefg"}), self.mock_http_conversation(
            http_config_fixture
        ):
            if http_fixture:
                with self.mock_http_conversation(http_fixture):
                    self.verify_reply(message, response)
            else:
                self.verify_reply(message, response)

    def test_normal(self):
        self._test('"hello" de', "Hallo (from Foo Test User)", "test_languages", "test_normal")

    def test_source_language_not_found(self):
        self._test(
            '"hello" german foo',
            (
                "Source language not found. Visit [here]"
                "(https://cloud.google.com/translate/docs/languages) for all languages"
            ),
            "test_languages",
        )

    def test_target_language_not_found(self):
        self._test(
            '"hello" bar english',
            (
                "Target language not found. Visit [here]"
                "(https://cloud.google.com/translate/docs/languages) for all languages"
            ),
            "test_languages",
        )

    def test_403(self):
        self._test(
            '"hello" german english',
            "Translate Error. Invalid API Key..",
            "test_languages",
            "test_403",
        )

    # Override default function in BotTestCase
    def test_bot_responds_to_empty_message(self):
        self._test("", help_text, "test_languages")

    def test_help_command(self):
        self._test("help", help_text, "test_languages")

    def test_help_too_many_args(self):
        self._test('"hello" de english foo bar', help_text, "test_languages")

    def test_help_no_langs(self):
        self._test('"hello"', help_text, "test_languages")

    def test_quotation_in_text(self):
        self._test(
            '"this has "quotation" marks in" english',
            'this has "quotation" marks in (from Foo Test User)',
            "test_languages",
            "test_quotation",
        )

    def test_exception(self):
        with patch(
            "zulip_bots.bots.google_translate.google_translate.translate", side_effect=Exception
        ):
            self._test('"hello" de', "Error. .", "test_languages")

    def test_invalid_api_key(self):
        with self.assertRaises(StubBotHandler.BotQuitError):
            self._test(None, None, "test_invalid_api_key")

    def test_api_access_not_configured(self):
        with self.assertRaises(StubBotHandler.BotQuitError):
            self._test(None, None, "test_api_access_not_configured")

    def test_connection_error(self):
        with patch("requests.post", side_effect=ConnectionError()), patch("logging.warning"):
            self._test('"test" en', "Could not connect to Google Translate. .", "test_languages")

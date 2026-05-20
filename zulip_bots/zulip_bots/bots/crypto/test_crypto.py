from zulip_bots.test_lib import BotTestCase, DefaultTests


class TestCryptoBot(BotTestCase, DefaultTests):
    bot_name = "crypto"

    # Test for correct behavior given proper crypto and date
    def test_normal_date(self):
        bot_response = "The market price for BTC on 2022-04-16 was $40554.6"

        with self.mock_http_conversation("test_normal_date"):
            self.verify_reply("BTC 2022-04-16", bot_response)

    # test for "current" price
    def test_normal_no_date(self):
        bot_response = "The current market price for BTC is $40696.73"

        with self.mock_http_conversation("test_normal_no_date"):
            self.verify_reply("BTC", bot_response)

    # test malformatted date
    def test_bad_date(self):
        bot_response = "Dates should be in the form YYYY-MM-DD."

        self.verify_reply("BTC 04-16-2022", bot_response)

    # test typo --> Not Found
    def test_400_error(self):
        bot_response = (
            "Sorry, I wasn't able to find anything on XYZ. "
            "Check your spelling and try again."
        )

        with self.mock_http_conversation("test_404"):
            self.verify_reply("XYZ", bot_response)

    # test empty message
    def test_no_inputs(self):
        bot_reponse = """
        This bot allows users to get spot prices for requested cryptocurrencies in USD.
        Users should @-mention the bot with the following format:
        @-mention <cryptocurrency abbreviation> <optional: date in format YYYY-MM-DD>
        i.e., "@-mention BTC 2022-04-16" or just "@-mention BTC"
        """

        self.verify_reply("", bot_reponse)

    # test too many arguments
    def test_too_many_inputs(self):
        bot_response = """
        This bot allows users to get spot prices for requested cryptocurrencies in USD.
        Users should @-mention the bot with the following format:
        @-mention <cryptocurrency abbreviation> <optional: date in format YYYY-MM-DD>
        i.e., "@-mention BTC 2022-04-16" or just "@-mention BTC"
        """

        self.verify_reply("BTC ETH 2022-04-16", bot_response)

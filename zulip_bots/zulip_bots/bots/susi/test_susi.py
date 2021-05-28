from zulip_bots.test_lib import BotTestCase, DefaultTests


class TestSusiBot(BotTestCase, DefaultTests):
    bot_name = "susi"

    def test_help(self) -> None:
        bot_response = """
    Hi, I am Susi, people generally ask me these questions:
    ```
    What is the exchange rate of USD to BTC
    How to cook biryani
    draw a card
    word starting with m and ending with v
    question me
    random GIF
    image of a bird
    flip a coin
    let us play
    who is Albert Einstein
    search wikipedia for artificial intelligence
    when is christmas
    what is hello in french
    name a popular movie
    news
    tell me a joke
    buy a dress
    currency of singapore
    distance between india and singapore
    tell me latest phone by LG
    ```
        """

        self.verify_reply("", bot_response)
        self.verify_reply("help", bot_response)

    def test_issue(self) -> None:
        request = "hi"
        bot_response = "Hello!"

        with self.mock_http_conversation("test_reply"):
            self.verify_reply(request, bot_response)

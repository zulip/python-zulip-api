from typing import Dict

import requests

from zulip_bots.lib import BotHandler


class SusiHandler:
    """
    Susi AI Bot
    To create and know more of SUSI skills go to `https://skills.susi.ai/`
    """

    def usage(self) -> str:
        return """
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

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        msg = message["content"]
        if msg in ("help", ""):
            bot_handler.send_reply(message, self.usage())
            return
        reply = requests.get("https://api.susi.ai/susi/chat.json", params=dict(q=msg))
        try:
            answer = reply.json()["answers"][0]["actions"][0]["expression"]
        except Exception:
            answer = "I don't understand. Can you rephrase?"
        bot_handler.send_reply(message, answer)


handler_class = SusiHandler

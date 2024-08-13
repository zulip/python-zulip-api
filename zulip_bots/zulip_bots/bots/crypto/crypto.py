# bot to fetch crypto information from coinbase API.
# No API key authentication is required for pricing
# and time information.

from datetime import datetime
from typing import Any, Dict

import requests
from requests.exceptions import ConnectionError, HTTPError

from zulip_bots.lib import BotHandler


class CryptoHandler:
    """
    This bot will get the current spot "market" exchange rate for a given
    cryptocurrency in USD.
    """
    def usage(self):
        return """
        This bot allows users to get spot prices for requested cryptocurrencies in USD.
        Users should @-mention the bot with the following format:
        @-mention <cryptocurrency abbreviation> <optional: date in format YYYY-MM-DD>
        i.e., "@-mention BTC 2022-04-16" or just "@-mention BTC"
        """

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler):
        original_content = message["content"]
        args = original_content.split()
        if len(args) == 0 or len(args) > 2:
            bot_handler.send_reply(message, self.usage())
            return

        date_param = None
        if len(args) == 2:
            date_param = {"date": args[1]}

        # check format of date input
        if date_param:
            format = "%Y-%m-%d"

            try:
                datetime.strptime(date_param["date"], format)
            except ValueError:
                reply = "Dates should be in the form YYYY-MM-DD."
                bot_handler.send_reply(message, reply)
                return

        currency_param = args[0]

        try:
            if date_param:
                response = requests.get(
                    "https://api.coinbase.com/v2/prices/{}-USD/spot".format(currency_param),
                    params=date_param
                )
            else:
                response = requests.get(
                    "https://api.coinbase.com/v2/prices/{}-USD/spot".format(currency_param)
                )

            # raise exception for bad status codes
            response.raise_for_status()
        except (HTTPError, ConnectionError):
            reply = (
                "Sorry, I wasn't able to find anything on {}. "
                "Check your spelling and try again."
            ).format(currency_param)

            bot_handler.send_reply(message, reply)
            return

        market_price = response.json()["data"]["amount"]

        if date_param:
            reply = (
                "The market price for {} on {} was ${}"
            ).format(currency_param, date_param["date"], market_price)
        else:
            reply = (
                "The current market price for {} is ${}"
            ).format(currency_param, market_price)

        bot_handler.send_reply(message, reply)


handler_class = CryptoHandler

import logging
from typing import Dict, Final, Optional

import requests

from zulip_bots.lib import BotHandler

# See readme.md for instructions on running this code.


class StackOverflowHandler:
    """
    This plugin facilitates searching Stack Overflow for a
    specific query and returns the top 3 questions from the
    search. It looks for messages starting with '@mention-bot'

    In this example, we write all Stack Overflow searches into
    the same stream that it was called from.
    """

    META: Final = {
        "name": "StackOverflow",
        "description": "Searches Stack Overflow for a query and returns the top 3 articles.",
    }

    def usage(self) -> str:
        return """
            This plugin will allow users to directly search
            Stack Overflow for a specific query and get the top 3
            articles that are returned from the search. Users
            should preface query with "@mention-bot".
            @mention-bot <search query>"""

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        bot_response = self.get_bot_stackoverflow_response(message, bot_handler)
        bot_handler.send_reply(message, bot_response)

    def get_bot_stackoverflow_response(
        self, message: Dict[str, str], bot_handler: BotHandler
    ) -> Optional[str]:
        """This function returns the URLs of the requested topic."""

        help_text = "Please enter your query after @mention-bot to search StackOverflow"

        # Checking if the link exists.
        query = message["content"]
        if query in ("", "help"):
            return help_text

        query_stack_url = "http://api.stackexchange.com/2.2/search/advanced"
        query_stack_params = dict(order="desc", sort="relevance", site="stackoverflow", title=query)
        try:
            data = requests.get(query_stack_url, params=query_stack_params)

        except requests.exceptions.RequestException:
            logging.error("broken link")
            return (
                "Uh-Oh ! Sorry ,couldn't process the request right now.:slightly_frowning_face:\n"
                "Please try again later."
            )

        # Checking if the bot accessed the link.
        if data.status_code != 200:
            logging.error("Page not found.")
            return (
                "Uh-Oh ! Sorry ,couldn't process the request right now.:slightly_frowning_face:\n"
                "Please try again later."
            )

        new_content = "For search term:" + query + "\n"

        # Checking if there is content for the searched term
        if len(data.json()["items"]) == 0:
            new_content = (
                "I am sorry. The search term you provided is not found :slightly_frowning_face:"
            )
        else:
            for i in range(min(3, len(data.json()["items"]))):
                search_string = data.json()["items"][i]["title"]
                link = data.json()["items"][i]["link"]
                new_content += str(i + 1) + " : " + "[" + search_string + "]" + "(" + link + ")\n"
        return new_content


handler_class = StackOverflowHandler

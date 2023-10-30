# See readme.md for instructions on running this code.
import logging
from typing import Dict, List

import requests
from bs4 import BeautifulSoup, Tag

from zulip_bots.lib import BotHandler


def google_search(keywords: str) -> List[Dict[str, str]]:
    query = {"q": keywords}
    # Gets the page
    page = requests.get("http://www.google.com/search", params=query)
    # Parses the page into BeautifulSoup
    soup = BeautifulSoup(page.text, "lxml")

    # Gets all search URLs
    search = soup.find(id="search")
    assert isinstance(search, Tag)
    anchors = search.findAll("a")
    results = []

    for a in anchors:
        try:
            # Tries to get the href property of the URL
            link = a["href"]
        except KeyError:
            continue
        # Link must start with '/url?', as these are the search result links
        if not link.startswith("/url?"):
            continue
        # Makes sure a hidden 'cached' result isn't displayed
        if a.text.strip() == "Cached" and "webcache.googleusercontent.com" in a["href"]:
            continue
        # a.text: The name of the page
        result = {"url": f"https://www.google.com{link}", "name": a.text}
        results.append(result)
    return results


def get_google_result(search_keywords: str) -> str:
    help_message = "To use this bot, start messages with @mentioned-bot, \
                    followed by what you want to search for. If \
                    found, Zulip will return the first search result \
                    on Google.\
                    \
                    An example message that could be sent is:\
                    '@mentioned-bot zulip' or \
                    '@mentioned-bot how to create a chatbot'."

    search_keywords = search_keywords.strip()

    if search_keywords in ("help", ""):
        return help_message
    else:
        try:
            results = google_search(search_keywords)
            if len(results) == 0:
                return "Found no results."
            return "Found Result: [{}]({})".format(results[0]["name"], results[0]["url"])
        except Exception as e:
            logging.exception("Error fetching Google results")
            return f"Error: Search failed. {e}."


class GoogleSearchHandler:
    """
    This plugin allows users to enter a search
    term in Zulip and get the top URL sent back
    to the context (stream or private) in which
    it was called. It looks for messages starting
    with @mentioned-bot.
    """

    def usage(self) -> str:
        return """
            This plugin will allow users to search
            for a given search term on Google from
            Zulip. Use '@mentioned-bot help' to get
            more information on the bot usage. Users
            should preface messages with
            @mentioned-bot.
            """

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        original_content = message["content"]
        result = get_google_result(original_content)
        bot_handler.send_reply(message, result)


handler_class = GoogleSearchHandler

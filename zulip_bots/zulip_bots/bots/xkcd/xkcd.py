import logging
import random
from typing import Dict, Final, Optional

import requests

from zulip_bots.lib import BotHandler

XKCD_TEMPLATE_URL = "https://xkcd.com/%s/info.0.json"
LATEST_XKCD_URL = "https://xkcd.com/info.0.json"


class XkcdHandler:
    """
    This plugin provides several commands that can be used for fetch a comic
    strip from https://xkcd.com. The bot looks for messages starting with
    "@mention-bot" and responds with a message with the comic based on provided
    commands.
    """

    META: Final = {
        "name": "XKCD",
        "description": "Fetches comic strips from https://xkcd.com.",
    }

    def usage(self) -> str:
        return """
            This plugin allows users to fetch a comic strip provided by
            https://xkcd.com. Users should preface the command with "@mention-bot".

            There are several commands to use this bot:
            - @mention-bot help -> To show all commands the bot supports.
            - @mention-bot latest -> To fetch the latest comic strip from xkcd.
            - @mention-bot random -> To fetch a random comic strip from xkcd.
            - @mention-bot <comic_id> -> To fetch a comic strip based on
            `<comic_id>`, e.g `@mention-bot 1234`.
            """

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        quoted_name = bot_handler.identity().mention
        xkcd_bot_response = get_xkcd_bot_response(message, quoted_name)
        bot_handler.send_reply(message, xkcd_bot_response)


class XkcdBotCommand:
    LATEST = 0
    RANDOM = 1
    COMIC_ID = 2


class XkcdNotFoundError(Exception):
    pass


class XkcdServerError(Exception):
    pass


def get_xkcd_bot_response(message: Dict[str, str], quoted_name: str) -> str:
    original_content = message["content"].strip()
    command = original_content.strip()

    commands_help = (
        "%s"
        f"\n* `{quoted_name} help` to show this help message."
        f"\n* `{quoted_name} latest` to fetch the latest comic strip from xkcd."
        f"\n* `{quoted_name} random` to fetch a random comic strip from xkcd."
        f"\n* `{quoted_name} <comic id>` to fetch a comic strip based on `<comic id>` "
        f"e.g `{quoted_name} 1234`."
    )

    try:
        if command == "help":
            return commands_help % ("xkcd bot supports these commands:",)
        elif command == "latest":
            fetched = fetch_xkcd_query(XkcdBotCommand.LATEST)
        elif command == "random":
            fetched = fetch_xkcd_query(XkcdBotCommand.RANDOM)
        elif command.isdigit():
            fetched = fetch_xkcd_query(XkcdBotCommand.COMIC_ID, command)
        else:
            return commands_help % (f"xkcd bot only supports these commands, not `{command}`:",)
    except (requests.exceptions.ConnectionError, XkcdServerError):
        logging.exception("Connection error occurred when trying to connect to xkcd server")
        return "Sorry, I cannot process your request right now, please try again later!"
    except XkcdNotFoundError:
        logging.exception(
            "XKCD server responded 404 when trying to fetch comic with id %s", command
        )
        return f"Sorry, there is likely no xkcd comic strip with id: #{command}"
    else:
        return "#{}: **{}**\n[{}]({})".format(
            fetched["num"],
            fetched["title"],
            fetched["alt"],
            fetched["img"],
        )


def fetch_xkcd_query(mode: int, comic_id: Optional[str] = None) -> Dict[str, str]:
    try:
        if mode == XkcdBotCommand.LATEST:  # Fetch the latest comic strip.
            url = LATEST_XKCD_URL

        elif mode == XkcdBotCommand.RANDOM:  # Fetch a random comic strip.
            latest = requests.get(LATEST_XKCD_URL)

            if latest.status_code != 200:
                raise XkcdServerError

            latest_id = latest.json()["num"]
            random_id = random.randint(1, latest_id)  # noqa: S311
            url = XKCD_TEMPLATE_URL % (str(random_id),)

        elif mode == XkcdBotCommand.COMIC_ID:  # Fetch specific comic strip by id number.
            if comic_id is None:
                raise TypeError("Missing comic_id argument")
            url = XKCD_TEMPLATE_URL % (comic_id,)

        fetched = requests.get(url)

        if fetched.status_code == 404:
            raise XkcdNotFoundError
        elif fetched.status_code != 200:
            raise XkcdServerError

        xkcd_json = fetched.json()
    except requests.exceptions.ConnectionError:
        logging.exception("Connection Error")
        raise

    return xkcd_json


handler_class = XkcdHandler

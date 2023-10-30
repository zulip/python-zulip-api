import logging
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.exceptions import ConnectionError

from zulip_bots.lib import BotHandler

USERS_LIST_URL = "https://api.flock.co/v1/roster.listContacts"
SEND_MESSAGE_URL = "https://api.flock.co/v1/chat.sendMessage"

help_message = """
You can send messages to any Flock user associated with your account from Zulip.
*Syntax*: **@botname to: message** where `to` is **firstName** of recipient.
"""


# Matches the recipient name provided by user with list of users in his contacts.
# If matches, returns the matched User's ID
def find_recipient_id(users: List[Any], recipient_name: str) -> str:
    for user in users:
        if recipient_name == user["firstName"]:
            return user["id"]


# Make request to given flock URL and return a two-element tuple
# whose left-hand value contains JSON body of response (or None if request failed)
# and whose right-hand value contains an error message (or None if request succeeded)
def make_flock_request(url: str, params: Dict[str, str]) -> Tuple[Any, str]:
    try:
        res = requests.get(url, params=params)
        return (res.json(), None)
    except ConnectionError:
        logging.exception("Error connecting to Flock")
        error = "Uh-Oh, couldn't process the request \
right now.\nPlease try again later"
        return (None, error)


# Returns two-element tuple whose left-hand value contains recipient
# user's ID (or None if it was not found) and right-hand value contains
# an error message (or None if recipient user's ID was found)
def get_recipient_id(
    recipient_name: str, config: Dict[str, str]
) -> Tuple[Optional[str], Optional[str]]:
    token = config["token"]
    payload = {"token": token}
    users, error = make_flock_request(USERS_LIST_URL, payload)
    if users is None:
        return (None, error)

    recipient_id = find_recipient_id(users, recipient_name)
    if recipient_id is None:
        error = "No user found. Make sure you typed it correctly."
        return (None, error)
    else:
        return (recipient_id, None)


# This handles the message sending work.
def get_flock_response(content: str, config: Dict[str, str]) -> str:
    token = config["token"]
    content_pieces = content.split(":")
    recipient_name = content_pieces[0].strip()
    message = content_pieces[1].strip()

    recipient_id, error = get_recipient_id(recipient_name, config)
    if recipient_id is None:
        return error

    if len(str(recipient_id)) > 30:
        return "Found user is invalid."

    payload = {"to": recipient_id, "text": message, "token": token}
    res, error = make_flock_request(SEND_MESSAGE_URL, payload)
    if res is None:
        return error

    if "uid" in res:
        return "Message sent."
    else:
        return "Message sending failed :slightly_frowning_face:. Please try again."


def get_flock_bot_response(content: str, config: Dict[str, str]) -> None:
    content = content.strip()
    if content in ("", "help"):
        return help_message
    else:
        result = get_flock_response(content, config)
        return result


class FlockHandler:
    """
    This is flock bot. Now you can send messages to any of your
    flock user without having to leave Zulip.
    """

    def initialize(self, bot_handler: BotHandler) -> None:
        self.config_info = bot_handler.get_config_info("flock")

    def usage(self) -> str:
        return """Hello from Flock Bot. You can send messages to any Flock user
right from Zulip."""

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        response = get_flock_bot_response(message["content"], self.config_info)
        bot_handler.send_reply(message, response)


handler_class = FlockHandler

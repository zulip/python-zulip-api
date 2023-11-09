import logging
from typing import Dict

import requests
from requests.exceptions import ConnectionError

from zulip_bots.lib import BotHandler

help_message = """
You can add datapoints towards your beeminder goals \
following the syntax shown below :smile:.\n \
\n**@mention-botname daystamp, value, comment**\
\n* `daystamp`**:** *yyyymmdd*  \
[**NOTE:** Optional field, default is *current daystamp*],\
\n* `value`**:** Enter a value [**NOTE:** Required field, can be any number],\
\n* `comment`**:** Add a comment [**NOTE:** Optional field, default is *None*]\
"""


def get_beeminder_response(message_content: str, config_info: Dict[str, str]) -> str:
    username = config_info["username"]
    goalname = config_info["goalname"]
    auth_token = config_info["auth_token"]

    message_content = message_content.strip()
    if message_content in ("", "help"):
        return help_message

    url = f"https://www.beeminder.com/api/v1/users/{username}/goals/{goalname}/datapoints.json"
    message_pieces = message_content.split(",")
    for i in range(len(message_pieces)):
        message_pieces[i] = message_pieces[i].strip()

    if len(message_pieces) == 1:
        payload = {"value": message_pieces[0], "auth_token": auth_token}
    elif len(message_pieces) == 2:
        if message_pieces[1].isdigit():
            payload = {
                "daystamp": message_pieces[0],
                "value": message_pieces[1],
                "auth_token": auth_token,
            }
        else:
            payload = {
                "value": message_pieces[0],
                "comment": message_pieces[1],
                "auth_token": auth_token,
            }
    elif len(message_pieces) == 3:
        payload = {
            "daystamp": message_pieces[0],
            "value": message_pieces[1],
            "comment": message_pieces[2],
            "auth_token": auth_token,
        }
    elif len(message_pieces) > 3:
        return "Make sure you follow the syntax.\n You can take a look \
at syntax by: @mention-botname help"

    try:
        r = requests.post(url, json=payload)

        if r.status_code != 200:
            if r.status_code == 401:  # Handles case of invalid key and missing key
                return "Error. Check your key!"
            else:
                return f"Error occured : {r.status_code}"  # Occures in case of unprocessable entity
        else:
            datapoint_link = f"https://www.beeminder.com/{username}/{goalname}"
            return f"[Datapoint]({datapoint_link}) created."  # Handles the case of successful datapoint creation
    except ConnectionError:
        logging.exception("Error connecting to Beeminder")
        return "Uh-Oh, couldn't process the request \
right now.\nPlease try again later"


class BeeminderHandler:
    """
    This plugin allows users to easily add datapoints
    towards their beeminder goals via zulip
    """

    def initialize(self, bot_handler: BotHandler) -> None:
        self.config_info = bot_handler.get_config_info("beeminder")
        # Check for valid auth_token
        auth_token = self.config_info["auth_token"]
        try:
            r = requests.get(
                "https://www.beeminder.com/api/v1/users/me.json", params={"auth_token": auth_token}
            )
            if r.status_code == 401:
                bot_handler.quit("Invalid key!")
        except ConnectionError:
            logging.exception("Error connecting to Beeminder")

    def usage(self) -> str:
        return "This plugin allows users to add datapoints towards their Beeminder goals"

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        response = get_beeminder_response(message["content"], self.config_info)
        bot_handler.send_reply(message, response)


handler_class = BeeminderHandler

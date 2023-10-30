# See readme.md for instructions on running this code.
import json
import logging
from typing import Dict

import apiai

from zulip_bots.lib import BotHandler

help_message = """DialogFlow bot
This bot will interact with dialogflow bots.
Simply send this bot a message, and it will respond depending on the configured bot's behaviour.
"""


def get_bot_result(message_content: str, config: Dict[str, str], sender_id: str) -> str:
    if message_content.strip() == "" or message_content.strip() == "help":
        return config["bot_info"]
    ai = apiai.ApiAI(config["key"])
    try:
        request = ai.text_request()
        request.session_id = sender_id
        request.query = message_content
        response = request.getresponse()
        res_str = response.read().decode("utf8", "ignore")
        res_json = json.loads(res_str)
        if res_json["status"]["errorType"] != "success" and "result" not in res_json:
            return "Error {}: {}.".format(
                res_json["status"]["code"], res_json["status"]["errorDetails"]
            )
        if res_json["result"]["fulfillment"]["speech"] == "":
            if (
                "alternateResult" in res_json
                and res_json["alternateResult"]["fulfillment"]["speech"] != ""
            ):
                return res_json["alternateResult"]["fulfillment"]["speech"]
            return "Error. No result."
        return res_json["result"]["fulfillment"]["speech"]
    except Exception as e:
        logging.exception("Error getting Dialogflow bot response")
        return f"Error. {e}."


class DialogFlowHandler:
    """
    This plugin allows users to easily add their own
    DialogFlow bots to zulip
    """

    def initialize(self, bot_handler: BotHandler) -> None:
        self.config_info = bot_handler.get_config_info("dialogflow")

    def usage(self) -> str:
        return """
            This plugin will allow users to easily add their own
            DialogFlow bots to zulip
            """

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        result = get_bot_result(message["content"], self.config_info, message["sender_id"])
        bot_handler.send_reply(message, result)


handler_class = DialogFlowHandler

import re
from typing import Any, Dict

import requests

from zulip_bots.lib import BotHandler


class FrontHandler:
    FRONT_API = "https://api2.frontapp.com/conversations/{}"
    COMMANDS = (
        ("archive", "Archive a conversation."),
        ("delete", "Delete a conversation."),
        ("spam", "Mark a conversation as spam."),
        ("open", "Restore a conversation."),
        ("comment <text>", "Leave a comment."),
    )
    CNV_ID_REGEXP = "cnv_(?P<id>[0-9a-z]+)"
    COMMENT_PREFIX = "comment "

    def usage(self) -> str:
        return """
            Front Bot uses the Front REST API to interact with Front. In order to use
            Front Bot, `front.conf` must be set up. See `doc.md` for more details.
            """

    def initialize(self, bot_handler: BotHandler) -> None:
        config = bot_handler.get_config_info("front")
        api_key = config.get("api_key")
        if not api_key:
            raise KeyError("No API key specified.")

        self.auth = "Bearer " + api_key

    def help(self, bot_handler: BotHandler) -> str:
        response = ""
        for command, description in self.COMMANDS:
            response += f"`{command}` {description}\n"

        return response

    def archive(self, bot_handler: BotHandler) -> str:
        response = requests.patch(
            self.FRONT_API.format(self.conversation_id),
            headers={"Authorization": self.auth},
            json={"status": "archived"},
        )

        if response.status_code not in (200, 204):
            return "Something went wrong."

        return "Conversation was archived."

    def delete(self, bot_handler: BotHandler) -> str:
        response = requests.patch(
            self.FRONT_API.format(self.conversation_id),
            headers={"Authorization": self.auth},
            json={"status": "deleted"},
        )

        if response.status_code not in (200, 204):
            return "Something went wrong."

        return "Conversation was deleted."

    def spam(self, bot_handler: BotHandler) -> str:
        response = requests.patch(
            self.FRONT_API.format(self.conversation_id),
            headers={"Authorization": self.auth},
            json={"status": "spam"},
        )

        if response.status_code not in (200, 204):
            return "Something went wrong."

        return "Conversation was marked as spam."

    def restore(self, bot_handler: BotHandler) -> str:
        response = requests.patch(
            self.FRONT_API.format(self.conversation_id),
            headers={"Authorization": self.auth},
            json={"status": "open"},
        )

        if response.status_code not in (200, 204):
            return "Something went wrong."

        return "Conversation was restored."

    def comment(self, bot_handler: BotHandler, **kwargs: Any) -> str:
        response = requests.post(
            self.FRONT_API.format(self.conversation_id) + "/comments",
            headers={"Authorization": self.auth},
            json=kwargs,
        )

        if response.status_code not in (200, 201):
            return "Something went wrong."

        return "Comment was sent."

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        command = message["content"]

        result = re.search(self.CNV_ID_REGEXP, message["subject"])
        if not result:
            bot_handler.send_reply(
                message,
                "No coversation ID found. Please make "
                "sure that the name of the topic "
                "contains a valid coversation ID.",
            )
            return None

        self.conversation_id = result.group()

        if command == "help":
            bot_handler.send_reply(message, self.help(bot_handler))

        elif command == "archive":
            bot_handler.send_reply(message, self.archive(bot_handler))

        elif command == "delete":
            bot_handler.send_reply(message, self.delete(bot_handler))

        elif command == "spam":
            bot_handler.send_reply(message, self.spam(bot_handler))

        elif command == "open":
            bot_handler.send_reply(message, self.restore(bot_handler))

        elif command.startswith(self.COMMENT_PREFIX):
            kwargs = {
                "author_id": "alt:email:" + message["sender_email"],
                "body": command[len(self.COMMENT_PREFIX) :],
            }
            bot_handler.send_reply(message, self.comment(bot_handler, **kwargs))
        else:
            bot_handler.send_reply(message, "Unknown command. Use `help` for instructions.")


handler_class = FrontHandler

# See readme.md for instructions on running this code.

from typing import Dict, Final

from zulip_bots.lib import BotHandler, use_storage


class IncrementorHandler:
    META: Final = {
        "name": "Incrementor",
        "description": "Example bot to test the update_message() function.",
    }

    def usage(self) -> str:
        return """
        This is a boilerplate bot that makes use of the
        update_message function. For the first @-mention, it initially
        replies with one message containing a `1`. Every time the bot
        is @-mentioned, this number will be incremented in the same message.
        """

    def initialize(self, bot_handler: BotHandler) -> None:
        storage = bot_handler.storage
        if not storage.contains("number") or not storage.contains("message_id"):
            storage.put("number", 0)
            storage.put("message_id", None)

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        with use_storage(bot_handler.storage, ["number"]) as storage:
            num = storage.get("number")

            # num should already be an int, but we do `int()` to force an
            # explicit type check
            num = int(num) + 1

            storage.put("number", num)
            if storage.get("message_id") is not None:
                result = bot_handler.update_message(
                    dict(message_id=storage.get("message_id"), content=str(num))
                )

                # When there isn't an error while updating the message, we won't
                # attempt to send the it again.
                if result is None or result.get("result") != "error":
                    return

            message_info = bot_handler.send_reply(message, str(num))
            if message_info is not None:
                storage.put("message_id", message_info["id"])


handler_class = IncrementorHandler

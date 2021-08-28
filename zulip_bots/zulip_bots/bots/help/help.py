# See readme.md for instructions on running this code.
from typing import Dict

from zulip_bots.lib import BotHandler


class HelpHandler:
    def usage(self) -> str:
        return """
            This plugin will give info about Zulip to
            any user that types a message saying "help".

            This is example code; ideally, you would flesh
            this out for more useful help pertaining to
            your Zulip instance.
            """

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        help_content = "Info on Zulip can be found here:\nhttps://github.com/zulip/zulip"
        bot_handler.send_reply(message, help_content)


handler_class = HelpHandler

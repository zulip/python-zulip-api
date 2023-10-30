# See readme.md for instructions on running this code.
from typing import Any, Dict

import packaged_helloworld
from zulip_bots.lib import BotHandler

__version__ = packaged_helloworld.__version__


class HelloWorldHandler:
    def usage(self) -> str:
        return """
        This is a boilerplate bot that responds to a user query with
        "beep boop", which is robot for "Hello World".

        This bot can be used as a template for other, more
        sophisticated, bots that can be installed separately.
        """

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        content = "beep boop"
        bot_handler.send_reply(message, content)

        emoji_name = "wave"
        bot_handler.react(message, emoji_name)


handler_class = HelloWorldHandler

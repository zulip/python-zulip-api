# See readme.md for instructions on running this code.

import importlib.abc
import importlib.util
from typing import Any, Callable, Dict, Optional

import wit

from zulip_bots.lib import BotHandler


class WitaiHandler:
    def usage(self) -> str:
        return """
        Wit.ai bot uses pywit API to interact with Wit.ai. In order to use
        Wit.ai bot, `witai.conf` must be set up. See `doc.md` for more details.
        """

    def initialize(self, bot_handler: BotHandler) -> None:
        config = bot_handler.get_config_info("witai")

        token = config.get("token")
        if not token:
            raise KeyError("No `token` was specified")

        # `handler_location` should be the location of a module which contains
        # the function `handle`. See `doc.md` for more details.
        handler_location = config.get("handler_location")
        if not handler_location:
            raise KeyError("No `handler_location` was specified")
        self.handle = get_handle(handler_location)

        help_message = config.get("help_message")
        if not help_message:
            raise KeyError("No `help_message` was specified")
        self.help_message = help_message

        self.client = wit.Wit(token)

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        if message["content"] == "" or message["content"] == "help":
            bot_handler.send_reply(message, self.help_message)
            return

        try:
            res = self.client.message(message["content"])
            message_for_user = self.handle(res)

            if message_for_user:
                bot_handler.send_reply(message, message_for_user)
        except wit.wit.WitError:
            bot_handler.send_reply(message, "Sorry, I don't know how to respond to that!")
        except Exception as e:
            bot_handler.send_reply(message, "Sorry, there was an internal error.")
            print(e)
            return


handler_class = WitaiHandler


def get_handle(location: str) -> Callable[[Dict[str, Any]], Optional[str]]:
    """Returns a function to be used when generating a response from Wit.ai
    bot. This function is the function named `handle` in the module at the
    given `location`. For an example of a `handle` function, see `doc.md`.

    For example,

        handle = get_handle('/Users/someuser/witai_handler.py')  # Get the handler function.
        res = witai_client.message(message['content'])  # Get the Wit.ai response.
        message_res = self.handle(res)  # Handle the response and find what to show the user.
        bot_handler.send_reply(message, message_res)  # Send it to the user.

    Parameters:
     - location: The absolute path to the module to look for `handle` in.
    """
    spec = importlib.util.spec_from_file_location("module.name", location)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not get handler from {location!r}.")
    handler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handler)
    return handler.handle

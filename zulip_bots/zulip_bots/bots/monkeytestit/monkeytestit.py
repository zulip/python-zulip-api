import logging
from typing import Dict, Any

from zulip_bots.bots.monkeytestit.lib import parse
from zulip_bots.lib import NoBotConfigException


class MonkeyTestitBot(object):
    def __init__(self):
        self.api_key = "None"
        self.config = None

    def usage(self):
        return "Remember to set your api_key first in the config. After " \
               "that, to perform a check, mention me and add the website.\n\n" \
               "Check doc.md for more options and setup instructions."

    def initialize(self, bot_handler: Any) -> None:
        try:
            self.config = bot_handler.get_config_info('monkeytestit')
        except NoBotConfigException:
            bot_handler.quit("Quitting because there's no config file "
                             "supplied. See doc.md for a guide on setting up "
                             "one. If you already know the drill, just create "
                             "a .conf file with \"monkeytestit\" as the "
                             "section header and api_key = <your key> for "
                             "the api key.")

        self.api_key = self.config.get('api_key')

        if not self.api_key:
            bot_handler.quit("Config file exists, but can't find api_key key "
                             "or value. Perhaps it is misconfigured. Check "
                             "doc.md for details on how to setup the config.")

        logging.info("Checking validity of API key. This will take a while.")

        if "wrong secret" in parse.execute("check https://website",
                                           self.api_key).lower():
            bot_handler.quit("API key exists, but it is not valid. Reconfigure"
                             " your api_key value and try again.")

    def handle_message(self, message: Dict[str, str],
                       bot_handler: Any) -> None:
        content = message['content']

        response = parse.execute(content, self.api_key)

        bot_handler.send_reply(message, response)


handler_class = MonkeyTestitBot

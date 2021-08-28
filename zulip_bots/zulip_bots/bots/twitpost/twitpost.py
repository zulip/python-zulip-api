from typing import Dict

import tweepy

from zulip_bots.lib import BotHandler


class TwitpostBot:
    def usage(self) -> str:
        return """ This bot posts on twitter from zulip chat itself.
                   Use '@twitpost help' to get more information
                   on the bot usage. """

    help_content = (
        "*Help for Twitter-post bot* :twitter: : \n\n"
        "The bot tweets on twitter when message starts "
        "with @twitpost.\n\n"
        "`@twitpost tweet <content>` will tweet on twitter "
        "with given `<content>`.\n"
        "Example:\n"
        " * @twitpost tweet hey batman\n"
    )

    def initialize(self, bot_handler: BotHandler) -> None:
        self.config_info = bot_handler.get_config_info("twitter")
        auth = tweepy.OAuthHandler(
            self.config_info["consumer_key"], self.config_info["consumer_secret"]
        )
        auth.set_access_token(
            self.config_info["access_token"], self.config_info["access_token_secret"]
        )
        self.api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        content = message["content"]

        if content.strip() == "":
            bot_handler.send_reply(message, "Please check help for usage.")
            return

        if content.strip() == "help":
            bot_handler.send_reply(message, self.help_content)
            return

        content = content.split()

        if len(content) > 1 and content[0] == "tweet":
            status = self.post(" ".join(content[1:]))
            screen_name = status["user"]["screen_name"]
            id_str = status["id_str"]
            bot_reply = f"https://twitter.com/{screen_name}/status/{id_str}"
            bot_reply = "Tweet Posted\n" + bot_reply
            bot_handler.send_reply(message, bot_reply)

    def post(self, text):
        return self.api.update_status(text)


handler_class = TwitpostBot

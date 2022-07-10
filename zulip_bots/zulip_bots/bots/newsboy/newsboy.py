from typing import Any, Dict, List, Optional

import requests

from zulip_bots.lib import BotHandler

INVALID_ARGUMENTS_ERROR_MESSAGE = "Invalid Arguments."
RESPONSE_ERROR_MESSAGE = "Invalid Response. Please check configuration and parameters."


class NewsboyHandler:
    def initialize(self, bot_handler: BotHandler) -> None:
        self.supported_commands = [
            ("help", "Get the bot usage information."),
            ("list-commands", "Get information about the commands supported by the bot."),
            ("get-top-news <country>", "Get top news of mention country e.g. (get-top-news us)."),
            ("list-countries", "Get the list of all supported countries."),
        ]
        self.config_info = bot_handler.get_config_info("newsboy")
        self.api_key = self.config_info["api_key"]

        self.check_api_key(bot_handler)

    def check_api_key(self, bot_handler: BotHandler) -> None:
        test_query_response = requests.get(
            "https://newsdata.io/api/1/news", params={"apikey": self.api_key}
        )
        try:
            if test_query_response.json()["status"] == "error":
                bot_handler.quit(
                    "Invalid Credentials. Please see doc.md to find out how to get them."
                )
        except AttributeError:
            pass

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:

        content = message["content"].strip().split()

        if content == []:
            bot_handler.send_reply(message, "Empty Query")
            return

        content[0] = content[0].lower()

        if content == ["help"]:
            bot_reply = self.usage()
        elif content == ["list-commands"]:
            bot_reply = self.get_all_supported_commands()
        elif content == ["list-countries"]:
            bot_reply = self.get_all_supported_countries()
        elif content[0] == "get-top-news":
            bot_reply = self.get_news_response(content, self.api_key)
        else:
            bot_reply = "Command not supported"

        bot_handler.send_reply(message, bot_reply)

    def get_news_response(self, content: List[str], api_key: str) -> Optional[str]:
        if len(content) < 2:
            return INVALID_ARGUMENTS_ERROR_MESSAGE

        base_url = "https://newsdata.io/api/1/news"
        country = content[1]

        params = {"apikey": api_key, "country": country, "q": "national", "language": "en"}
        try:
            response = requests.get(base_url, params=params).json()
            data = response["results"] if response["status"] == "success" else None

            for dt in data:
                try:
                    title = dt["title"]
                    descr = dt["description"]
                    link = dt["link"]
                    image = dt["image_url"]
                    if (
                        title is not None
                        and descr is not None
                        and link is not None
                        and image is not None
                    ):
                        return f"## [{title}]({link})\n\n > ***{descr}*** "
                except Exception:
                    continue
        except Exception as e:
            return (RESPONSE_ERROR_MESSAGE, str(e))

    def get_all_supported_countries(self) -> str:
        countries = """
            Argentina - ar \n
            Australia - au \n
            Austria - at \n
            Belgium - be \n
            Brazil - br \n
            Bulgaria - bg \n
            Canada - ca \n
            China - cn \n
            Colombia - co \n
            Cuba - cu \n
            Czech republic - cz \n
            Egypt - eg \n
            France - fr \n
            Germany - de \n
            Greece - gr \n
            Hong kong - hk \n
            Hungary - hu \n
            India - in \n
            Indonesia - id \n
            Ireland - ie \n
            Israel - il \n
            Italy - it \n
            Japan - jp \n
            Kazakhstan - kz \n
            Latvia - lv \n
            Lebanon - lb \n
            Lithuania - lt \n
            Malaysia - my \n
            Mexico - mx \n
            Morocco - ma \n
            Netherland - nl \n
            New zealand - nz \n
            Nigeria - ng \n
            North korea - kp \n
            Norway - no \n
            Pakistan - pk \n
            Peru - pe \n
            Philippines - ph \n
            Poland - pl \n
            Portugal - pt \n
            Romania - ro \n
            Russia - ru \n
            Saudi arabia - sa \n
            Serbia - rs \n
            Singapore - sg \n
            Slovakia - sk \n
            Slovenia - si \n
            South africa - za \n
            South korea - kr \n
            Spain - es \n
            Sweden - se \n
            Switzerland - ch \n
            Taiwan - tw \n
            Thailand - th \n
            Turkey - tr \n
            Ukraine - ua \n
            United arab emirates - ae \n
            United kingdom - gb \n
            United states of america - us \n
            Venezuela - ve \n
            """
        return countries

    def get_all_supported_commands(self) -> str:
        bot_response = "**Commands:** \n"
        for index, (command, desc) in enumerate(self.supported_commands):
            bot_response += f"{index + 1}. **{command}**: {desc}\n"

        return bot_response

    def usage(self) -> str:
        help_content = """
        ## Newsboy
        The Newsboy bot is a Zulip bot that fetches the top national news of particular country and
        displays it to the user with headline and short description.

        Use `list-commands` to get information about the supported commands.

        Usage:
        `get-top-news <country-abbreviation>` e.g. `get-top-news us`
        """
        return help_content


handler_class = NewsboyHandler

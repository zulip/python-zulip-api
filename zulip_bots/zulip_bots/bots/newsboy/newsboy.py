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
                bot_handler.quit("Invalid Credentials. Please see doc.md to find out how to get them.")
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
                        return (
                            f"## [{title}]({link})\n\n > ***{descr}*** "
                        )
                except Exception:
                    continue
        except Exception as e:
            return (RESPONSE_ERROR_MESSAGE, str(e))

    def get_all_supported_countries(self) -> str:
        countries = """
            Argentina - ar 
            Australia - au 
            Austria - at 
            Belgium - be 
            Brazil - br 
            Bulgaria - bg 
            Canada - ca 
            China - cn 
            Colombia - co 
            Cuba - cu 
            Czech republic - cz 
            Egypt - eg 
            France - fr 
            Germany - de 
            Greece - gr 
            Hong kong - hk 
            Hungary - hu 
            India - in 
            Indonesia - id 
            Ireland - ie 
            Israel - il 
            Italy - it 
            Japan - jp 
            Kazakhstan - kz 
            Latvia - lv 
            Lebanon - lb 
            Lithuania - lt 
            Malaysia - my 
            Mexico - mx 
            Morocco - ma 
            Netherland - nl 
            New zealand - nz 
            Nigeria - ng 
            North korea - kp 
            Norway - no 
            Pakistan - pk 
            Peru - pe 
            Philippines - ph 
            Poland - pl 
            Portugal - pt 
            Romania - ro 
            Russia - ru 
            Saudi arabia - sa 
            Serbia - rs 
            Singapore - sg 
            Slovakia - sk 
            Slovenia - si 
            South africa - za 
            South korea - kr 
            Spain - es 
            Sweden - se 
            Switzerland - ch 
            Taiwan - tw 
            Thailand - th 
            Turkey - tr 
            Ukraine - ua 
            United arab emirates - ae 
            United kingdom - gb 
            United states of america - us 
            Venezuela - ve"""
        return countries

    def get_all_supported_commands(self) -> str:
        bot_response = "**Commands:** \n"
        for index, (command, desc) in enumerate(self.supported_commands):
            bot_response += f"{index + 1}. **{command}**: {desc}\n"

        return bot_response

    def usage(self) -> str:
        help_content =  """
        ## Newsboy
        The Newsboy bot is a Zulip bot that fetches the top national news of particular country and 
        displays it to the user with headline and short description.

        Use `list-commands` to get information about the supported commands.

        Usage:
        `get-top-news <country-abbreviation>` e.g. `get-top-news us`
        """
        return help_content


handler_class = NewsboyHandler

# See readme.md for instructions on running this code.

from typing import Any, Dict, List

import requests

from zulip_bots.lib import BotHandler


class MentionHandler:
    def initialize(self, bot_handler: BotHandler) -> None:
        self.config_info = bot_handler.get_config_info("mention")
        self.access_token = self.config_info["access_token"]
        self.account_id = ""

        self.check_access_token(bot_handler)

    def check_access_token(self, bot_handler: BotHandler) -> None:
        test_query_header = {
            "Authorization": "Bearer " + self.access_token,
            "Accept-Version": "1.15",
        }
        test_query_response = requests.get(
            "https://api.mention.net/api/accounts/me", headers=test_query_header
        )

        try:
            test_query_data = test_query_response.json()
            if (
                test_query_data["error"] == "invalid_grant"
                and test_query_data["error_description"] == "The access token provided is invalid."
            ):
                bot_handler.quit(
                    "Access Token Invalid. Please see doc.md to find out how to get it."
                )
        except KeyError:
            pass

    def usage(self) -> str:
        return """
        This is a Mention API Bot which will find mentions
        of the given keyword throughout the web.
        Version 1.00
        """

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        message["content"] = message["content"].strip()

        if message["content"].lower() == "help":
            bot_handler.send_reply(message, self.usage())
            return

        if message["content"] == "":
            bot_handler.send_reply(message, "Empty Mention Query")
            return

        keyword = message["content"]
        content = self.generate_response(keyword)
        bot_handler.send_reply(message, content)

    def get_account_id(self) -> str:
        get_ac_id_header = {
            "Authorization": "Bearer " + self.access_token,
            "Accept-Version": "1.15",
        }
        response = requests.get("https://api.mention.net/api/accounts/me", headers=get_ac_id_header)
        data_json = response.json()
        account_id = data_json["account"]["id"]
        return account_id

    def get_alert_id(self, keyword: str) -> str:
        create_alert_header = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/json",
            "Accept-Version": "1.15",
        }

        create_alert_data: Any = {
            "name": keyword,
            "query": {"type": "basic", "included_keywords": [keyword]},
            "languages": ["en"],
            "sources": ["web"],
        }

        response = requests.post(
            "https://api.mention.net/api/accounts/" + self.account_id + "/alerts",
            data=create_alert_data,
            headers=create_alert_header,
        )
        data_json = response.json()
        alert_id = data_json["alert"]["id"]
        return alert_id

    def get_mentions(self, alert_id: str) -> List[Any]:
        get_mentions_header = {
            "Authorization": "Bearer " + self.access_token,
            "Accept-Version": "1.15",
        }
        response = requests.get(
            "https://api.mention.net/api/accounts/"
            + self.account_id
            + "/alerts/"
            + alert_id
            + "/mentions",
            headers=get_mentions_header,
        )
        data_json = response.json()
        mentions = data_json["mentions"]
        return mentions

    def generate_response(self, keyword: str) -> str:
        if self.account_id == "":
            self.account_id = self.get_account_id()

        try:
            alert_id = self.get_alert_id(keyword)
        except (TypeError, KeyError) as e:
            # Usually triggered by invalid token or json parse error when account quote is finished.
            raise MentionNoResponseError from e

        try:
            mentions = self.get_mentions(alert_id)
        except (TypeError, KeyError) as e:
            # Usually triggered by no response or json parse error when account quota is finished.
            raise MentionNoResponseError from e

        reply = "The most recent mentions of `" + keyword + "` on the web are: \n"
        for mention in mentions:
            reply += "[{title}]({id})\n".format(title=mention["title"], id=mention["original_url"])
        return reply


handler_class = MentionHandler


class MentionNoResponseError(Exception):
    pass

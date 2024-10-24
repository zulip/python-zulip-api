# See readme.md for instructions on running this code.

import logging
import re
from typing import Any, Collection, Dict, List

# Upstream issue with simple_salesforce
# https://github.com/simple-salesforce/simple-salesforce/issues/723
from simple_salesforce import Salesforce  # type: ignore[attr-defined]
from simple_salesforce.exceptions import SalesforceAuthenticationFailed

from zulip_bots.bots.salesforce.utils import commands, default_query, link_query, object_types
from zulip_bots.lib import BotHandler

base_help_text = """Salesforce bot
This bot can do simple salesforce query requests
**All commands must be @-mentioned to the bot.**
Commands:
{}
Arguments:
**-limit <num>**: the maximum number of entries sent (default: 5)
**-show**: show all the properties of each entry (default: false)

This bot can also show details about any Salesforce links sent to it.

Supported Object types:
These are the types of Salesforce object supported by this bot.
The bot cannot show the details of any other object types.
{}"""

login_url = "https://login.salesforce.com/"


def get_help_text() -> str:
    command_text = ""
    for command in commands:
        if "template" in command and "description" in command:
            command_text += "**{}**: {}\n".format(
                "{} [arguments]".format(command["template"]), command["description"]
            )
    object_type_text = ""
    for object_type in object_types.values():
        object_type_text += "{}\n".format(object_type["table"])
    return base_help_text.format(command_text, object_type_text)


def format_result(
    result: Dict[str, Any],
    exclude_keys: Collection[str] = [],
    force_keys: Collection[str] = [],
    rank_output: bool = False,
    show_all_keys: bool = False,
) -> str:
    exclude_keys = {*exclude_keys, "Name", "attributes", "Id"}
    output = ""
    if result["totalSize"] == 0:
        return "No records found."
    if result["totalSize"] == 1:
        record = result["records"][0]
        output += "**[{}]({}{})**\n".format(record["Name"], login_url, record["Id"])
        for key, value in record.items():
            if key not in exclude_keys:
                output += f">**{key}**: {value}\n"
    else:
        for i, record in enumerate(result["records"]):
            if rank_output:
                output += f"{i + 1}) "
            output += "**[{}]({}{})**\n".format(record["Name"], login_url, record["Id"])
            added_keys = False
            for key, value in record.items():
                if key in force_keys or (show_all_keys and key not in exclude_keys):
                    added_keys = True
                    output += f">**{key}**: {value}\n"
            if added_keys:
                output += "\n"
    return output


def query_salesforce(arg: str, salesforce: Salesforce, command: Dict[str, Any]) -> str:
    arg = arg.strip()
    qarg = arg.split(" -", 1)[0]
    split_args: List[str] = []
    raw_arg = ""
    if len(arg.split(" -", 1)) > 1:
        raw_arg = " -" + arg.split(" -", 1)[1]
        split_args = raw_arg.split(" -")
    limit_num = 5
    re_limit = re.compile(r"-limit \d+")
    limit = re_limit.search(raw_arg)
    if limit:
        limit_num = int(limit.group().rsplit(" ", 1)[1])
        logging.info("Searching with limit %d", limit_num)
    query = default_query
    if "query" in command:
        query = command["query"]
    object_type = object_types[command["object"]]
    res = salesforce.query(
        query.format(object_type["fields"], object_type["table"], qarg, limit_num)
    )
    exclude_keys: List[str] = []
    if "exclude_keys" in command:
        exclude_keys = command["exclude_keys"]
    force_keys: List[str] = []
    if "force_keys" in command:
        force_keys = command["force_keys"]
    rank_output = False
    if "rank_output" in command:
        rank_output = command["rank_output"]
    show_all_keys = "show" in split_args
    if "show_all_keys" in command:
        show_all_keys = command["show_all_keys"] or "show" in split_args
    return format_result(
        res,
        exclude_keys=exclude_keys,
        force_keys=force_keys,
        rank_output=rank_output,
        show_all_keys=show_all_keys,
    )


def get_salesforce_link_details(link: str, sf: Any) -> str:
    re_id = re.compile("/[A-Za-z0-9]{18}")
    re_id_res = re_id.search(link)
    if re_id_res is None:
        return "Invalid salesforce link"
    id = re_id_res.group().strip("/")
    for object_type in object_types.values():
        res = sf.query(link_query.format(object_type["fields"], object_type["table"], id))
        if res["totalSize"] == 1:
            return format_result(res)
    return "No object found. Make sure it is of the supported types. Type `help` for more info."


class SalesforceHandler:
    def usage(self) -> str:
        return """
        This is a Salesforce bot, which can search for Contacts,
        Accounts and Opportunities. And can be configured for any
        other object types.

        It will also show details of any Salesforce links posted.

        @-mention the bot with 'help' to see available commands.
        """

    def get_salesforce_response(self, content: str) -> str:
        content = content.strip()
        if content in ("", "help"):
            return get_help_text()
        if content.startswith("http") and "force" in content:
            return get_salesforce_link_details(content, self.sf)
        for command in commands:
            for command_keyword in command["commands"]:
                if content.startswith(command_keyword):
                    args = content.replace(command_keyword, "").strip()
                    if args != "":
                        if "callback" in command:
                            return command["callback"](args, self.sf, command)
                        else:
                            return query_salesforce(args, self.sf, command)
                    else:
                        return "Usage: {} [arguments]".format(command["template"])
        return get_help_text()

    def initialize(self, bot_handler: BotHandler) -> None:
        self.config_info = bot_handler.get_config_info("salesforce")
        try:
            self.sf = Salesforce(
                username=self.config_info["username"],
                password=self.config_info["password"],
                security_token=self.config_info["security_token"],
            )
        except SalesforceAuthenticationFailed as err:
            bot_handler.quit(f"Failed to log in to Salesforce. {err.code} {err.message}")

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        try:
            bot_response = self.get_salesforce_response(message["content"])
            bot_handler.send_reply(message, bot_response)
        except Exception as e:
            bot_handler.send_reply(message, f"Error. {e}.", bot_response)


handler_class = SalesforceHandler

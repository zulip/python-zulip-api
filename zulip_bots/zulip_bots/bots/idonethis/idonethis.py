import logging
import re
from typing import Any, Dict, List, Optional

import requests

from zulip_bots.lib import BotHandler

API_BASE_URL = "https://beta.idonethis.com/api/v2"

api_key = ""
default_team = ""


class AuthenticationException(Exception):
    pass


class TeamNotFoundException(Exception):
    def __init__(self, team: str) -> None:
        self.team = team


class UnknownCommandSyntax(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail


class UnspecifiedProblemException(Exception):
    pass


def make_API_request(
    endpoint: str,
    method: str = "GET",
    body: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
) -> Any:
    headers = {"Authorization": "Token " + api_key}
    if method == "GET":
        r = requests.get(API_BASE_URL + endpoint, headers=headers, params=params)
    elif method == "POST":
        r = requests.post(API_BASE_URL + endpoint, headers=headers, params=params, json=body)
    if r.status_code == 200:
        return r.json()
    elif (
        r.status_code == 401
        and "error" in r.json()
        and r.json()["error"] == "Invalid API Authentication"
    ):
        logging.error("Error authenticating, please check key " + str(r.url))
        raise AuthenticationException()
    else:
        logging.error("Error make API request, code " + str(r.status_code) + ". json: " + r.json())
        raise UnspecifiedProblemException()


def api_noop() -> None:
    make_API_request("/noop")


def api_list_team() -> List[Dict[str, str]]:
    return make_API_request("/teams")


def api_show_team(hash_id: str) -> Dict[str, str]:
    return make_API_request(f"/teams/{hash_id}")


# NOTE: This function is not currently used
def api_show_users(hash_id: str) -> Any:
    return make_API_request(f"/teams/{hash_id}/members")


def api_list_entries(team_id: Optional[str] = None) -> List[Dict[str, Any]]:
    if team_id:
        return make_API_request("/entries", params=dict(team_id=team_id))
    else:
        return make_API_request("/entries")


def api_create_entry(body: str, team_id: str) -> Dict[str, Any]:
    return make_API_request("/entries", "POST", {"body": body, "team_id": team_id})


def list_teams() -> str:
    response = ["Teams:"] + [" * " + team["name"] for team in api_list_team()]
    return "\n".join(response)


def get_team_hash(team_name: str) -> str:
    for team in api_list_team():
        if team["name"].lower() == team_name.lower() or team["hash_id"] == team_name:
            return team["hash_id"]
    raise TeamNotFoundException(team_name)


def team_info(team_name: str) -> str:
    data = api_show_team(get_team_hash(team_name))
    return "\n".join(["Team Name: {name}", "ID: `{hash_id}`", "Created at: {created_at}"]).format(
        **data
    )


def entries_list(team_name: str) -> str:
    if team_name:
        data = api_list_entries(get_team_hash(team_name))
        response = f"Entries for {team_name}:"
    else:
        data = api_list_entries()
        response = "Entries for all teams:"
    for entry in data:
        response += "\n".join(
            [
                "",
                " * {body_formatted}",
                "  * Created at: {created_at}",
                "  * Status: {status}",
                "  * User: {username}",
                "  * Team: {teamname}",
                "  * ID: {hash_id}",
            ]
        ).format(username=entry["user"]["full_name"], teamname=entry["team"]["name"], **entry)
    return response


def create_entry(message: str) -> str:
    SINGLE_WORD_REGEX = re.compile("--team=([a-zA-Z0-9_]*)")
    MULTIWORD_REGEX = re.compile('"--team=([^"]*)"')

    team = ""
    new_message = ""
    single_word_match = SINGLE_WORD_REGEX.search(message)
    multiword_match = MULTIWORD_REGEX.search(message)

    if multiword_match is not None:
        team = multiword_match.group(1)
        new_message = MULTIWORD_REGEX.sub("", message).strip()
    elif single_word_match is not None:
        team = single_word_match.group(1)
        new_message = SINGLE_WORD_REGEX.sub("", message).strip()
    elif default_team:
        team = default_team
        new_message = message
    else:
        raise UnknownCommandSyntax(
            """I don't know which team you meant for me to create an entry under.
Either set a default team or pass the `--team` flag.
More information in my help"""
        )

    team_id = get_team_hash(team)
    data = api_create_entry(new_message, team_id)
    return "Great work :thumbs_up:. New entry `{}` created!".format(data["body_formatted"])


class IDoneThisHandler:
    def initialize(self, bot_handler: BotHandler) -> None:
        global api_key, default_team
        self.config_info = bot_handler.get_config_info("idonethis")
        if "api_key" in self.config_info:
            api_key = self.config_info["api_key"]
        else:
            logging.error("An API key must be specified for this bot to run.")
            logging.error(
                "Have a look at the Setup section of my documenation for more information."
            )
            bot_handler.quit()

        if "default_team" in self.config_info:
            default_team = self.config_info["default_team"]
        else:
            logging.error(
                "Cannot find default team. Users will need to manually specify a team each time an entry is created."
            )

        try:
            api_noop()
        except AuthenticationException:
            logging.error(
                "Authentication exception with idonethis. Can you check that your API keys are correct? "
            )
            bot_handler.quit()
        except UnspecifiedProblemException:
            logging.error("Problem connecting to idonethis. Please check connection")
            bot_handler.quit()

    def usage(self) -> str:
        default_team_message = ""
        if default_team:
            default_team_message = "The default team is currently set as `" + default_team + "`."
        else:
            default_team_message = "There is currently no default team set up :frowning:."
        return (
            """
This bot allows for interaction with idonethis, a collaboration tool to increase a team's productivity.
Below are some of the commands you can use, and what they do.

`<team>` can either be the name or ID of a team.

 * `@mention help` view this help message
 * `@mention list teams`
    List all the teams
 * `@mention team info <team>`
    Show information about one `<team>`
 * `@mention list entries`
    List entries from any team
 * `@mention list entries <team>`
    List all entries from `<team>`
 * `@mention new entry` or `@mention i did`
    Create a new entry. Optionally supply `--team=<team>` for teams with no spaces or `"--team=<team>"`
    for teams with spaces. For example `@mention i did "--team=product team" something` will create a
    new entry `something` for the product team.
        """
            + default_team_message
        )

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        bot_handler.send_reply(message, self.get_response(message))

    def get_response(self, message: Dict[str, Any]) -> str:
        message_content = message["content"].strip().split()
        reply = ""
        try:
            command = " ".join(message_content[:2])
            if command in ["teams list", "list teams"]:
                reply = list_teams()
            elif command in ["teams info", "team info"]:
                if len(message_content) > 2:
                    reply = team_info(" ".join(message_content[2:]))
                else:
                    raise UnknownCommandSyntax(
                        "You must specify the team in which you request information from."
                    )
            elif command in ["entries list", "list entries"]:
                reply = entries_list(" ".join(message_content[2:]))
            elif command in ["entries create", "create entry", "new entry", "i did"]:
                reply = create_entry(" ".join(message_content[2:]))
            elif command in ["help"]:
                reply = self.usage()
            else:
                raise UnknownCommandSyntax("I can't understand the command you sent me :confused: ")
        except TeamNotFoundException as e:
            reply = (
                "Sorry, it doesn't seem as if I can find a team named `" + e.team + "` :frowning:."
            )
        except AuthenticationException:
            reply = "I can't currently authenticate with idonethis. "
            reply += "Can you check that your API key is correct? For more information see my documentation."
        except UnknownCommandSyntax as e:
            reply = (
                "Sorry, I don't understand what your trying to say. Use `@mention help` to see my help. "
                + e.detail
            )
        except Exception as e:  # catches UnspecifiedProblemException, and other problems
            reply = "Oh dear, I'm having problems processing your request right now. Perhaps you could try again later :grinning:"
            logging.error("Exception caught: " + str(e))
        return reply


handler_class = IDoneThisHandler

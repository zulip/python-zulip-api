import logging
import re
from typing import Any, Dict, Tuple, Union

import requests

from zulip_bots.lib import BotHandler


class GithubHandler:
    """
    This bot provides details on github issues and pull requests when they're
    referenced in the chat.
    """

    GITHUB_ISSUE_URL_TEMPLATE = "https://api.github.com/repos/{owner}/{repo}/issues/{id}"
    HANDLE_MESSAGE_REGEX = re.compile(r"(?:([\w-]+)\/)?([\w-]+)?#(\d+)")

    def initialize(self, bot_handler: BotHandler) -> None:
        self.config_info = bot_handler.get_config_info("github_detail", optional=True)
        self.owner = self.config_info.get("owner", False)
        self.repo = self.config_info.get("repo", False)

    def usage(self) -> str:
        return (
            "This plugin displays details on github issues and pull requests. "
            "To reference an issue or pull request usename mention the bot then "
            "anytime in the message type its id, for example:\n"
            "@**Github detail** #3212 zulip#3212 zulip/zulip#3212\n"
            "The default owner is {} and the default repo is {}.".format(self.owner, self.repo)
        )

    def format_message(self, details: Dict[str, Any]) -> str:
        number = details["number"]
        title = details["title"]
        link = details["html_url"]
        author = details["user"]["login"]
        owner = details["owner"]
        repo = details["repo"]

        description = details["body"]
        status = details["state"].title()

        message_string = (
            f"**[{owner}/{repo}#{number}]",
            f"({link}) - {title}**\n",
            "Created by **[{author}](https://github.com/{author})**\n".format(author=author),
            "Status - **{status}**\n```quote\n{description}\n```".format(
                status=status, description=description
            ),
        )
        return "".join(message_string)

    def get_details_from_github(
        self, owner: str, repo: str, number: str
    ) -> Union[None, Dict[str, Union[str, int, bool]]]:
        # Gets the details of an issues or pull request
        try:
            r = requests.get(
                self.GITHUB_ISSUE_URL_TEMPLATE.format(owner=owner, repo=repo, id=number)
            )
        except requests.exceptions.RequestException as e:
            logging.exception(str(e))
            return None
        if r.status_code != requests.codes.ok:
            return None
        return r.json()

    def get_owner_and_repo(self, issue_pr: Any) -> Tuple[str, str]:
        owner = issue_pr.group(1)
        repo = issue_pr.group(2)
        if owner is None:
            owner = self.owner
            if repo is None:
                repo = self.repo
        return (owner, repo)

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        # Send help message
        if message["content"] == "help":
            bot_handler.send_reply(message, self.usage())
            return

        # Capture owner, repo, id
        issue_prs = list(re.finditer(self.HANDLE_MESSAGE_REGEX, message["content"]))
        bot_messages = []
        if len(issue_prs) > 5:
            # We limit to 5 requests to prevent denial-of-service
            bot_message = "Please ask for <=5 links in any one request"
            bot_handler.send_reply(message, bot_message)
            return

        for issue_pr in issue_prs:
            owner, repo = self.get_owner_and_repo(issue_pr)
            if owner and repo:
                details = self.get_details_from_github(owner, repo, issue_pr.group(3))
                if details is not None:
                    details["owner"] = owner
                    details["repo"] = repo
                    bot_messages.append(self.format_message(details))
                else:
                    bot_messages.append(
                        "Failed to find issue/pr: {owner}/{repo}#{id}".format(
                            owner=owner, repo=repo, id=issue_pr.group(3)
                        )
                    )
            else:
                bot_messages.append("Failed to detect owner and repository name.")
        if len(bot_messages) == 0:
            bot_messages.append("Failed to find any issue or PR.")
        bot_message = "\n".join(bot_messages)
        bot_handler.send_reply(message, bot_message)


handler_class = GithubHandler

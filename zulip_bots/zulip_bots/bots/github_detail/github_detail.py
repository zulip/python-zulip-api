import re
import os
import sys
import logging
import configparser

import requests

from typing import Dict, Any, Tuple, Union

class GithubHandler(object):
    '''
    This bot provides details on github issues and pull requests when they're
    referenced in the chat.
    '''

    GITHUB_ISSUE_URL_TEMPLATE = 'https://api.github.com/repos/{owner}/{repo}/issues/{id}'
    ISSUE_PR_NUMBER_REGEX = re.compile("(?:([\w-]+)\/)?([\w-]+)?#(\d+)")

    GITHUB_RAW_FILE_CONTENT_URL_TEMPLATE = 'https://raw.githubusercontent.com/{owner}/{repo}/{path}'
    GITHUB_REPO_URL_REGEX = re.compile('^(http|https|git)://(www\.|)github.com/(?P<owner>([^/]+))/'
                                       '(?P<repository>([^/]+))/(?P<type>([^/]+))/'
                                       '(?P<path>([^#]+))(?P<lines>(|#.*))$')

    def initialize(self, bot_handler: Any) -> None:
        self.config_info = bot_handler.get_config_info('github_detail', optional=True)
        self.owner = self.config_info.get("owner", False)
        self.repo = self.config_info.get("repo", False)

    def usage(self) -> str:
        return ("* **Get PR/issue details:**This plugin displays details on github issues and pull requests. "
                "To reference an issue or pull request usename mention the bot then "
                "anytime in the message type its id, for example:\n"
                "@**Github detail** #3212 zulip#3212 zulip/zulip#3212\n"
                "The default owner is {} and the default repo is {}."
                "\n* **Get a file's contents:**Give a full url to get the line contents"
                "\nSend an valid  URL to a GitHub file to get its contents."
                "\nUse the line numbers to get only the specific lines from the file.\n"
                "Example: `@**Github detail**` https://github.com/zulip/zulip/blob/"
                "master/zerver/apps.py#L10-L12".format(self.owner, self.repo))

    def format_message(self, details: Dict[str, Any]) -> str:
        number = details['number']
        title = details['title']
        link = details['html_url']
        author = details['user']['login']
        owner = details['owner']
        repo = details['repo']

        description = details['body']
        status = details['state'].title()

        message_string = ('**[{owner}/{repo}#{id}]'.format(owner=owner, repo=repo, id=number),
                          '({link}) - {title}**\n'.format(title=title, link=link),
                          'Created by **[{author}](https://github.com/{author})**\n'.format(author=author),
                          'Status - **{status}**\n```quote\n{description}\n```'.format(status=status, description=description))
        return ''.join(message_string)

    def get_details_from_github(self, owner: str, repo: str, number: str) -> Union[None, Dict[str, Union[str, int, bool]]]:
        # Gets the details of an issues or pull request
        try:
            r = requests.get(
                self.GITHUB_ISSUE_URL_TEMPLATE.format(owner=owner, repo=repo, id=number))
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

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        # Send help message
        if message['content'] == 'help':
            bot_handler.send_reply(message, self.usage())
            return
        reply = ''
        try:
            # Try and match if a GitHub URL is present in the message
            url_details = self.get_file_url_match(message['content'])
            if url_details and url_details['type'] == 'blob':
                reply = self.get_file_contents(**url_details)
            else:
                # Try and match the `owner/repo#123` type issue or PR number
                reply = self.match_pr_and_get_reply(message['content'])

            bot_handler.send_reply(message, reply or 'I couldn\'t process that message.'
                                                     'Try replying `help` to know what I can do.')
        except Exception as e:
            logging.exception(str(e))
            bot_handler.send_reply(message, ':dizzy:  Something unexpected happened!')

    def match_pr_and_get_reply(self, message_content):
        # Capture owner, repo, id
        issue_prs = list(re.finditer(
            self.ISSUE_PR_NUMBER_REGEX, message_content))
        bot_messages = []
        if len(issue_prs) > 5:
            # We limit to 5 requests to prevent denial-of-service
            bot_message = 'Please ask for <=5 links in any one request'
            return bot_message

        for issue_pr in issue_prs:
            owner, repo = self.get_owner_and_repo(issue_pr)
            if owner and repo:
                details = self.get_details_from_github(owner, repo, issue_pr.group(3))
                if details is not None:
                    details['owner'] = owner
                    details['repo'] = repo
                    bot_messages.append(self.format_message(details))
                else:
                    bot_messages.append("Failed to find issue/pr: {owner}/{repo}#{id}"
                                        .format(owner=owner, repo=repo, id=issue_pr.group(3)))
            else:
                bot_messages.append("Failed to detect owner and repository name.")
        if len(bot_messages) == 0:
            return None
        bot_message = '\n'.join(bot_messages)
        return bot_message

    def get_file_url_match(self, message_content):
            details = re.match(self.GITHUB_REPO_URL_REGEX, message_content)
            return details.groupdict() if details is not None else None

    def get_file_contents(self, owner, repository, path, lines, **kwargs):
        url = self.GITHUB_RAW_FILE_CONTENT_URL_TEMPLATE.format(owner=owner,
                                                               repo=repository,
                                                               path=path)
        try:
            raw_file = requests.get(url)
            raw_file.raise_for_status()
        except requests.exceptions.RequestException as e:
            return 'An error occurred while trying to fetch the contents of the file :oh_no: \n' \
                'Are you sure the URL is correct ?'

        if lines:
            line_number_regex = re.compile('^#L(?P<start>(\d+))(|-L(?P<end>(\d+)))$')
            line_number_match = re.match(line_number_regex, lines)
            if line_number_match:
                # Decrementing to select the index in a list
                start = int(line_number_match.group('start'))-1

                # Sometimes, the ending line number might be missing(i.e only one line has been selected)
                # In that case we set it to start+1 (so the list can be sliced correctly)
                end = line_number_match.group('end') or start+1
                end = int(end)
                lines_as_list = raw_file.text.split('\n')
                reply = '\n'.join(lines_as_list[start:end])
                return '**[{}](https://www.github.com/blob/{}):** *{} - {}*\n' \
                       '```\n\n{}\n```'.format(path, path, start+1, end, reply)
        else:
            return '**[{}](https://www.github.com/blob/{}):**\n' \
                   '```\n{}\n```'.format(path, path, raw_file.text)

handler_class = GithubHandler

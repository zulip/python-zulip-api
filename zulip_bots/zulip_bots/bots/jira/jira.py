import base64
import re
from typing import Any, Dict, Optional

import requests

from zulip_bots.lib import BotHandler

GET_REGEX = re.compile('get "(?P<issue_key>.+)"$')
CREATE_REGEX = re.compile(
    'create issue "(?P<summary>.+?)"'
    ' in project "(?P<project_key>.+?)"'
    ' with type "(?P<type_name>.+?)"'
    '( with description "(?P<description>.+?)")?'
    '( assigned to "(?P<assignee>.+?)")?'
    '( with priority "(?P<priority_name>.+?)")?'
    '( labeled "(?P<labels>.+?)")?'
    '( due "(?P<due_date>.+?)")?'
    "$"
)
EDIT_REGEX = re.compile(
    'edit issue "(?P<issue_key>.+?)"'
    '( to use summary "(?P<summary>.+?)")?'
    '( to use project "(?P<project_key>.+?)")?'
    '( to use type "(?P<type_name>.+?)")?'
    '( to use description "(?P<description>.+?)")?'
    '( by assigning to "(?P<assignee>.+?)")?'
    '( to use priority "(?P<priority_name>.+?)")?'
    '( by labeling "(?P<labels>.+?)")?'
    '( by making due "(?P<due_date>.+?)")?'
    "$"
)
SEARCH_REGEX = re.compile('search "(?P<search_term>.+)"$')
JQL_REGEX = re.compile('jql "(?P<jql_query>.+)"$')
HELP_REGEX = re.compile("help$")

HELP_RESPONSE = """
**get**

`get` takes in an issue key and sends back information about that issue. For example,

you:

 > @**Jira Bot** get "BOTS-13"

Jira Bot:

 > **Issue *BOTS-13*: Create Jira Bot**
 >
 > - Type: *Task*
 > - Description:
 > > Jira Bot would connect to Jira.
 > - Creator: *admin*
 > - Project: *Bots*
 > - Priority: *Medium*
 > - Status: *To Do*

---

**search**

`search` takes in a search term and returns issues with matching summaries. For example,

you:

 > @**Jira Bot** search "XSS"

Jira Bot:

 > **Search results for *"XSS"*:**
 >
 > - ***BOTS-5:*** Stored XSS **[Published]**
 > - ***BOTS-6:*** Reflected XSS **[Draft]**

---

**jql**

`jql` takes in a jql search string and returns matching issues. For example,

you:

 > @**Jira Bot** jql "issuetype = Engagement ORDER BY created DESC"

Jira Bot:

 > **Search results for *"issuetype = Engagement ORDER BY created DESC"*:**
 >
 > - ***BOTS-1:*** External Website Test **[In Progress]**
 > - ***BOTS-3:*** Network Vulnerability Scan **[Draft]**

---

**create**

`create` creates an issue using its

 - summary,
 - project,
 - type,
 - description *(optional)*,
 - assignee *(optional)*,
 - priority *(optional)*,
 - labels *(optional)*, and
 - due date *(optional)*

For example, to create an issue with every option,

you:

 > @**Jira Bot** create issue "Make an issue" in project "BOTS"' with type \
"Task" with description "This is a description" assigned to "skunkmb" with \
priority "Medium" labeled "issues, testing" due "2017-01-23"

Jira Bot:

 > Issue *BOTS-16* is up! https://example.atlassian.net/browse/BOTS-16

---

**edit**

`edit` is like create, but changes an existing issue using its

 - summary,
 - project *(optional)*,
 - type *(optional)*,
 - description *(optional)*,
 - assignee *(optional)*,
 - priority *(optional)*,
 - labels *(optional)*, and
 - due date *(optional)*.

For example, to change every part of an issue,

you:

 > @**Jira Bot** edit issue "BOTS-16" to use summary "Change the summary" \
to use project "NEWBOTS" to use type "Bug" to use description "This is \
a new description" by assigning to "admin" to use priority "Low" by \
labeling "new, labels" by making due "2018-12-5"

Jira Bot:

 > Issue *BOTS-16* was edited! https://example.atlassian.net/browse/BOTS-16
"""


class JiraHandler:
    def usage(self) -> str:
        return """
        Jira Bot uses the Jira REST API to interact with Jira. In order to use
        Jira Bot, `jira.conf` must be set up. See `doc.md` for more details.
        """

    def initialize(self, bot_handler: BotHandler) -> None:
        config = bot_handler.get_config_info("jira")

        username = config.get("username")
        password = config.get("password")
        domain = config.get("domain")
        if not username:
            raise KeyError("No `username` was specified")
        if not password:
            raise KeyError("No `password` was specified")
        if not domain:
            raise KeyError("No `domain` was specified")

        self.auth = make_jira_auth(username, password)

        # Allow users to override the HTTP scheme
        if re.match(r"^https?://", domain, re.IGNORECASE):
            self.domain_with_protocol = domain
        else:
            self.domain_with_protocol = "https://" + domain

        # Use the front facing URL in output
        self.display_url = config.get("display_url")
        if not self.display_url:
            self.display_url = self.domain_with_protocol

    def jql_search(self, jql_query: str) -> str:
        unknown_val = "*unknown*"
        jira_response = requests.get(
            self.domain_with_protocol
            + f"/rest/api/2/search?jql={jql_query}&fields=key,summary,status",
            headers={"Authorization": self.auth},
        ).json()

        url = self.display_url + "/browse/"
        errors = jira_response.get("errorMessages", [])
        results = jira_response.get("total", 0)

        if errors:
            response = "Oh no! Jira raised an error:\n > " + ", ".join(errors)
        else:
            response = f"*Found {results} results*\n\n"
            for issue in jira_response.get("issues", []):
                fields = issue.get("fields", {})
                summary = fields.get("summary", unknown_val)
                status_name = fields.get("status", {}).get("name", unknown_val)
                response += "\n - {}: [{}]({}) **[{}]**".format(
                    issue["key"], summary, url + issue["key"], status_name
                )

        return response

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        content = message.get("content")
        response = ""

        get_match = GET_REGEX.match(content)
        create_match = CREATE_REGEX.match(content)
        edit_match = EDIT_REGEX.match(content)
        search_match = SEARCH_REGEX.match(content)
        jql_match = JQL_REGEX.match(content)
        help_match = HELP_REGEX.match(content)

        if get_match:
            unknown_val = "*unknown*"

            key = get_match.group("issue_key")

            jira_response = requests.get(
                self.domain_with_protocol + "/rest/api/2/issue/" + key,
                headers={"Authorization": self.auth},
            ).json()

            url = self.display_url + "/browse/" + key
            errors = jira_response.get("errorMessages", [])
            fields = jira_response.get("fields", {})

            creator_name = fields.get("creator", {}).get("name", unknown_val)
            description = fields.get("description", unknown_val)
            priority_name = fields.get("priority", {}).get("name", unknown_val)
            project_name = fields.get("project", {}).get("name", unknown_val)
            type_name = fields.get("issuetype", {}).get("name", unknown_val)
            status_name = fields.get("status", {}).get("name", unknown_val)
            summary = fields.get("summary", unknown_val)

            if errors:
                response = "Oh no! Jira raised an error:\n > " + ", ".join(errors)
            else:
                response = (
                    f"**Issue *[{key}]({url})*: {summary}**\n\n"
                    f" - Type: *{type_name}*\n"
                    " - Description:\n"
                    f" > {description}\n"
                    f" - Creator: *{creator_name}*\n"
                    f" - Project: *{project_name}*\n"
                    f" - Priority: *{priority_name}*\n"
                    f" - Status: *{status_name}*\n"
                )
        elif create_match:
            jira_response = requests.post(
                self.domain_with_protocol + "/rest/api/2/issue",
                headers={"Authorization": self.auth},
                json=make_create_json(
                    create_match.group("summary"),
                    create_match.group("project_key"),
                    create_match.group("type_name"),
                    create_match.group("description"),
                    create_match.group("assignee"),
                    create_match.group("priority_name"),
                    create_match.group("labels"),
                    create_match.group("due_date"),
                ),
            )

            jira_response_json = jira_response.json() if jira_response.text else {}

            key = jira_response_json.get("key", "")
            url = self.display_url + "/browse/" + key
            errors = list(jira_response_json.get("errors", {}).values())
            if errors:
                response = "Oh no! Jira raised an error:\n > " + ", ".join(errors)
            else:
                response = "Issue *" + key + "* is up! " + url
        elif edit_match and check_is_editing_something(edit_match):
            key = edit_match.group("issue_key")

            jira_response = requests.put(
                self.domain_with_protocol + "/rest/api/2/issue/" + key,
                headers={"Authorization": self.auth},
                json=make_edit_json(
                    edit_match.group("summary"),
                    edit_match.group("project_key"),
                    edit_match.group("type_name"),
                    edit_match.group("description"),
                    edit_match.group("assignee"),
                    edit_match.group("priority_name"),
                    edit_match.group("labels"),
                    edit_match.group("due_date"),
                ),
            )

            jira_response_json = jira_response.json() if jira_response.text else {}

            url = self.display_url + "/browse/" + key
            errors = list(jira_response_json.get("errors", {}).values())
            if errors:
                response = "Oh no! Jira raised an error:\n > " + ", ".join(errors)
            else:
                response = "Issue *" + key + "* was edited! " + url
        elif search_match:
            search_term = search_match.group("search_term")
            search_results = self.jql_search(f"summary ~ {search_term}")
            response = f'**Search results for "{search_term}"**\n\n{search_results}'
        elif jql_match:
            jql_query = jql_match.group("jql_query")
            search_results = self.jql_search(jql_query)
            response = f'**Search results for "{jql_query}"**\n\n{search_results}'
        elif help_match:
            response = HELP_RESPONSE
        else:
            response = "Sorry, I don't understand that! Send me `help` for instructions."

        bot_handler.send_reply(message, response)


def make_jira_auth(username: str, password: str) -> str:
    """Makes an auth header for Jira in the form 'Basic: <encoded credentials>'.

    Parameters:
     - username: The Jira email address.
     - password: The Jira password.
    """
    combo = username + ":" + password
    encoded = base64.b64encode(combo.encode("utf-8")).decode("utf-8")
    return "Basic " + encoded


def make_create_json(
    summary: str,
    project_key: str,
    type_name: str,
    description: Optional[str],
    assignee: Optional[str],
    priority_name: Optional[str],
    labels: Optional[str],
    due_date: Optional[str],
) -> Any:
    """Makes a JSON string for the Jira REST API editing endpoint based on
    fields that could be edited.

    Parameters:
     - summary: The Jira summary property.
     - project_key: The Jira project key property.
     - type_name (optional): The Jira type name property.
     - description (optional): The Jira description property.
     - assignee (optional): The Jira assignee property.
     - priority_name (optional): The Jira priority name property.
     - labels (optional): The Jira labels property, as a string of labels separated by
                          comma-spaces.
     - due_date (optional): The Jira due date property.
    """
    json_fields = {
        "summary": summary,
        "project": {"key": project_key},
        "issuetype": {"name": type_name},
    }
    if description:
        json_fields["description"] = description
    if assignee:
        json_fields["assignee"] = {"name": assignee}
    if priority_name:
        json_fields["priority"] = {"name": priority_name}
    if labels:
        json_fields["labels"] = labels.split(", ")
    if due_date:
        json_fields["duedate"] = due_date

    json = {"fields": json_fields}

    return json


def make_edit_json(
    summary: Optional[str],
    project_key: Optional[str],
    type_name: Optional[str],
    description: Optional[str],
    assignee: Optional[str],
    priority_name: Optional[str],
    labels: Optional[str],
    due_date: Optional[str],
) -> Any:
    """Makes a JSON string for the Jira REST API editing endpoint based on
    fields that could be edited.

    Parameters:
     - summary (optional): The Jira summary property.
     - project_key (optional): The Jira project key property.
     - type_name (optional): The Jira type name property.
     - description (optional): The Jira description property.
     - assignee (optional): The Jira assignee property.
     - priority_name (optional): The Jira priority name property.
     - labels (optional): The Jira labels property, as a string of labels separated by
                          comma-spaces.
     - due_date (optional): The Jira due date property.
    """
    json_fields = {}

    if summary:
        json_fields["summary"] = summary
    if project_key:
        json_fields["project"] = {"key": project_key}
    if type_name:
        json_fields["issuetype"] = {"name": type_name}
    if description:
        json_fields["description"] = description
    if assignee:
        json_fields["assignee"] = {"name": assignee}
    if priority_name:
        json_fields["priority"] = {"name": priority_name}
    if labels:
        json_fields["labels"] = labels.split(", ")
    if due_date:
        json_fields["duedate"] = due_date

    json = {"fields": json_fields}

    return json


def check_is_editing_something(match: Any) -> bool:
    """Checks if an editing match is actually going to do editing. It is
    possible for an edit regex to match without doing any editing because each
    editing field is optional. For example, 'edit issue "BOTS-13"' would pass
    but wouldn't preform any actions.

    Parameters:
     - match: The regex match object.
    """
    return bool(
        match.group("summary")
        or match.group("project_key")
        or match.group("type_name")
        or match.group("description")
        or match.group("assignee")
        or match.group("priority_name")
        or match.group("labels")
        or match.group("due_date")
    )


handler_class = JiraHandler

import base64
import re
import requests
from typing import Any, Dict, Iterable, Optional

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
    '$'
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
    '$'
)
HELP_REGEX = re.compile('help$')

HELP_RESPONSE = '''
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
'''

class JiraHandler(object):
    def usage(self) -> str:
        return '''
        Jira Bot uses the Jira REST API to interact with Jira. In order to use
        Jira Bot, `jira.conf` must be set up. See `doc.md` for more details.
        '''

    def initialize(self, bot_handler: Any) -> None:
        config = bot_handler.get_config_info('jira')

        username = config.get('username')
        password = config.get('password')
        domain = config.get('domain')
        if not username:
            raise KeyError('No `username` was specified')
        if not password:
            raise KeyError('No `password` was specified')
        if not domain:
            raise KeyError('No `domain` was specified')

        self.auth = make_jira_auth(username, password)
        self.domain_with_protocol = 'https://' + domain

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        content = message.get('content')
        response = ''

        get_match = GET_REGEX.match(content)
        create_match = CREATE_REGEX.match(content)
        edit_match = EDIT_REGEX.match(content)
        help_match = HELP_REGEX.match(content)

        if get_match:
            UNKNOWN_VAL = '*unknown*'

            key = get_match.group('issue_key')

            jira_response = requests.get(
                self.domain_with_protocol + '/rest/api/2/issue/' + key,
                headers={'Authorization': self.auth},
            ).json()

            url = self.domain_with_protocol + '/browse/' + key
            errors = jira_response.get('errorMessages', [])
            fields = jira_response.get('fields', {})

            creator_name = fields.get('creator', {}).get('name', UNKNOWN_VAL)
            description = fields.get('description', UNKNOWN_VAL)
            priority_name = fields.get('priority', {}).get('name', UNKNOWN_VAL)
            project_name = fields.get('project', {}).get('name', UNKNOWN_VAL)
            type_name = fields.get('issuetype', {}).get('name', UNKNOWN_VAL)
            status_name = fields.get('status', {}).get('name', UNKNOWN_VAL)
            summary = fields.get('summary', UNKNOWN_VAL)

            if errors:
                response = 'Oh no! Jira raised an error:\n > ' + ', '.join(errors)
            else:
                response = (
                    '**Issue *[{0}]({1})*: {2}**\n\n'
                    ' - Type: *{3}*\n'
                    ' - Description:\n'
                    ' > {4}\n'
                    ' - Creator: *{5}*\n'
                    ' - Project: *{6}*\n'
                    ' - Priority: *{7}*\n'
                    ' - Status: *{8}*\n'
                ).format(key, url, summary, type_name, description, creator_name, project_name,
                         priority_name, status_name)
        elif create_match:
            jira_response = requests.post(
                self.domain_with_protocol + '/rest/api/2/issue',
                headers={'Authorization': self.auth},
                json=make_create_json(create_match.group('summary'),
                                      create_match.group('project_key'),
                                      create_match.group('type_name'),
                                      create_match.group('description'),
                                      create_match.group('assignee'),
                                      create_match.group('priority_name'),
                                      create_match.group('labels'),
                                      create_match.group('due_date'))
            )

            jira_response_json = jira_response.json() if jira_response.text else {}

            key = jira_response_json.get('key', '')
            url = self.domain_with_protocol + '/browse/' + key
            errors = list(jira_response_json.get('errors', {}).values())
            if errors:
                response = 'Oh no! Jira raised an error:\n > ' + ', '.join(errors)
            else:
                response = 'Issue *' + key + '* is up! ' + url
        elif edit_match and check_is_editing_something(edit_match):
            key = edit_match.group('issue_key')

            jira_response = requests.put(
                self.domain_with_protocol + '/rest/api/2/issue/' + key,
                headers={'Authorization': self.auth},
                json=make_edit_json(edit_match.group('summary'),
                                    edit_match.group('project_key'),
                                    edit_match.group('type_name'),
                                    edit_match.group('description'),
                                    edit_match.group('assignee'),
                                    edit_match.group('priority_name'),
                                    edit_match.group('labels'),
                                    edit_match.group('due_date'))
            )

            jira_response_json = jira_response.json() if jira_response.text else {}

            url = self.domain_with_protocol + '/browse/' + key
            errors = list(jira_response_json.get('errors', {}).values())
            if errors:
                response = 'Oh no! Jira raised an error:\n > ' + ', '.join(errors)
            else:
                response = 'Issue *' + key + '* was edited! ' + url
        elif help_match:
            response = HELP_RESPONSE
        else:
            response = 'Sorry, I don\'t understand that! Send me `help` for instructions.'

        bot_handler.send_reply(message, response)

def make_jira_auth(username: str, password: str) -> str:
    '''Makes an auth header for Jira in the form 'Basic: <encoded credentials>'.

    Parameters:
     - username: The Jira email address.
     - password: The Jira password.
    '''
    combo = username + ':' + password
    encoded = base64.b64encode(combo.encode('utf-8')).decode('utf-8')
    return 'Basic ' + encoded

def make_create_json(summary: str, project_key: str, type_name: str,
                     description: Optional[str], assignee: Optional[str],
                     priority_name: Optional[str], labels: Optional[str],
                     due_date: Optional[str]) -> Any:
    '''Makes a JSON string for the Jira REST API editing endpoint based on
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
    '''
    json_fields = {
        'summary': summary,
        'project': {
            'key': project_key
        },
        'issuetype': {
            'name': type_name
        }
    }
    if description:
        json_fields['description'] = description
    if assignee:
        json_fields['assignee'] = {'name': assignee}
    if priority_name:
        json_fields['priority'] = {'name': priority_name}
    if labels:
        json_fields['labels'] = labels.split(', ')
    if due_date:
        json_fields['duedate'] = due_date

    json = {'fields': json_fields}

    return json

def make_edit_json(summary: Optional[str], project_key: Optional[str],
                   type_name: Optional[str], description: Optional[str],
                   assignee: Optional[str], priority_name: Optional[str],
                   labels: Optional[str], due_date: Optional[str]) -> Any:
    '''Makes a JSON string for the Jira REST API editing endpoint based on
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
    '''
    json_fields = {}

    if summary:
        json_fields['summary'] = summary
    if project_key:
        json_fields['project'] = {'key': project_key}
    if type_name:
        json_fields['issuetype'] = {'name': type_name}
    if description:
        json_fields['description'] = description
    if assignee:
        json_fields['assignee'] = {'name': assignee}
    if priority_name:
        json_fields['priority'] = {'name': priority_name}
    if labels:
        json_fields['labels'] = labels.split(', ')
    if due_date:
        json_fields['duedate'] = due_date

    json = {'fields': json_fields}

    return json

def check_is_editing_something(match: Any) -> bool:
    '''Checks if an editing match is actually going to do editing. It is
    possible for an edit regex to match without doing any editing because each
    editing field is optional. For example, 'edit issue "BOTS-13"' would pass
    but wouldn't preform any actions.

    Parameters:
     - match: The regex match object.
    '''
    return bool(
        match.group('summary') or
        match.group('project_key') or
        match.group('type_name') or
        match.group('description') or
        match.group('assignee') or
        match.group('priority_name') or
        match.group('labels') or
        match.group('due_date')
    )

handler_class = JiraHandler

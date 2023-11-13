from typing import Final

from typing_extensions import override

from zulip_bots.test_lib import BotTestCase, DefaultTests


class TestJiraBot(BotTestCase, DefaultTests):
    bot_name = "jira"

    MOCK_CONFIG_INFO: Final = {
        "username": "example@example.com",
        "password": "qwerty!123",
        "domain": "example.atlassian.net",
    }

    MOCK_SCHEME_CONFIG_INFO: Final = {
        "username": "example@example.com",
        "password": "qwerty!123",
        "domain": "http://example.atlassian.net",
    }

    MOCK_DISPLAY_CONFIG_INFO: Final = {
        "username": "example@example.com",
        "password": "qwerty!123",
        "domain": "example.atlassian.net",
        "display_url": "http://test.com",
    }

    MOCK_GET_RESPONSE = """\
**Issue *[TEST-13](https://example.atlassian.net/browse/TEST-13)*: summary**

 - Type: *Task*
 - Description:
 > description
 - Creator: *admin*
 - Project: *Tests*
 - Priority: *Medium*
 - Status: *To Do*
"""

    MOCK_CREATE_RESPONSE = "Issue *TEST-16* is up! https://example.atlassian.net/browse/TEST-16"

    MOCK_EDIT_RESPONSE = "Issue *TEST-16* was edited! https://example.atlassian.net/browse/TEST-16"

    MOCK_NOTHING_RESPONSE = "Sorry, I don't understand that! Send me `help` for instructions."

    MOCK_HELP_RESPONSE = """
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

    MOCK_SEARCH_RESPONSE = '**Search results for "TEST"**\n\n*Found 2 results*\n\n\n - TEST-1: [summary test 1](https://example.atlassian.net/browse/TEST-1) **[To Do]**\n - TEST-2: [summary test 2](https://example.atlassian.net/browse/TEST-2) **[To Do]**'
    MOCK_SEARCH_RESPONSE_URL = '**Search results for "TEST"**\n\n*Found 2 results*\n\n\n - TEST-1: [summary test 1](http://test.com/browse/TEST-1) **[To Do]**\n - TEST-2: [summary test 2](http://test.com/browse/TEST-2) **[To Do]**'
    MOCK_SEARCH_RESPONSE_SCHEME = '**Search results for "TEST"**\n\n*Found 2 results*\n\n\n - TEST-1: [summary test 1](http://example.atlassian.net/browse/TEST-1) **[To Do]**\n - TEST-2: [summary test 2](http://example.atlassian.net/browse/TEST-2) **[To Do]**'
    MOCK_JQL_RESPONSE = '**Search results for "summary ~ TEST"**\n\n*Found 2 results*\n\n\n - TEST-1: [summary test 1](https://example.atlassian.net/browse/TEST-1) **[To Do]**\n - TEST-2: [summary test 2](https://example.atlassian.net/browse/TEST-2) **[To Do]**'

    def _test_invalid_config(self, invalid_config, error_message) -> None:
        with self.mock_config_info(invalid_config), self.assertRaisesRegex(KeyError, error_message):
            bot, bot_handler = self._get_handlers()

    def test_config_without_username(self) -> None:
        config_without_username = {
            "password": "qwerty!123",
            "domain": "example.atlassian.net",
        }
        self._test_invalid_config(config_without_username, "No `username` was specified")

    def test_config_without_password(self) -> None:
        config_without_password = {
            "username": "example@example.com",
            "domain": "example.atlassian.net",
        }
        self._test_invalid_config(config_without_password, "No `password` was specified")

    def test_config_without_domain(self) -> None:
        config_without_domain = {
            "username": "example@example.com",
            "password": "qwerty!123",
        }
        self._test_invalid_config(config_without_domain, "No `domain` was specified")

    def test_get(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO), self.mock_http_conversation("test_get"):
            self.verify_reply('get "TEST-13"', self.MOCK_GET_RESPONSE)

    def test_get_error(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO), self.mock_http_conversation(
            "test_get_error"
        ):
            self.verify_reply('get "TEST-13"', "Oh no! Jira raised an error:\n > error1")

    def test_create(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO), self.mock_http_conversation(
            "test_create"
        ):
            self.verify_reply(
                'create issue "Testing" in project "TEST" with type "Task"',
                self.MOCK_CREATE_RESPONSE,
            )

    def test_create_error(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO), self.mock_http_conversation(
            "test_create_error"
        ):
            self.verify_reply(
                'create issue "Testing" in project "TEST" with type "Task" '
                'with description "This is a test description" assigned to "testuser" '
                'with priority "Medium" labeled "issues, testing" due "2018-06-11"',
                "Oh no! Jira raised an error:\n > error1",
            )

    def test_edit(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO), self.mock_http_conversation("test_edit"):
            self.verify_reply(
                'edit issue "TEST-16" to use description "description"', self.MOCK_EDIT_RESPONSE
            )

    def test_edit_error(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO), self.mock_http_conversation(
            "test_edit_error"
        ):
            self.verify_reply(
                'edit issue "TEST-13" to use summary "Change the summary" '
                'to use project "TEST" to use type "Bug" to use description "This is a test description" '
                'by assigning to "testuser" to use priority "Low" by labeling "issues, testing" '
                'by making due "2018-06-11"',
                "Oh no! Jira raised an error:\n > error1",
            )

    def test_search(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO), self.mock_http_conversation(
            "test_search"
        ):
            self.verify_reply('search "TEST"', self.MOCK_SEARCH_RESPONSE)

    def test_jql(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO), self.mock_http_conversation(
            "test_search"
        ):
            self.verify_reply('jql "summary ~ TEST"', self.MOCK_JQL_RESPONSE)

    def test_search_url(self) -> None:
        with self.mock_config_info(self.MOCK_DISPLAY_CONFIG_INFO), self.mock_http_conversation(
            "test_search"
        ):
            self.verify_reply('search "TEST"', self.MOCK_SEARCH_RESPONSE_URL)

    def test_search_scheme(self) -> None:
        with self.mock_config_info(self.MOCK_SCHEME_CONFIG_INFO), self.mock_http_conversation(
            "test_search_scheme"
        ):
            self.verify_reply('search "TEST"', self.MOCK_SEARCH_RESPONSE_SCHEME)

    def test_help(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO):
            self.verify_reply("help", self.MOCK_HELP_RESPONSE)

    @override
    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO):
            self.verify_reply("", self.MOCK_NOTHING_RESPONSE)

    def test_no_command(self) -> None:
        with self.mock_config_info(self.MOCK_CONFIG_INFO):
            self.verify_reply("qwertyuiop", self.MOCK_NOTHING_RESPONSE)

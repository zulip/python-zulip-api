from typing import Final

from typing_extensions import override

from zulip_bots.test_file_utils import get_bot_message_handler
from zulip_bots.test_lib import BotTestCase, DefaultTests, StubBotHandler


class TestGithubDetailBot(BotTestCase, DefaultTests):
    bot_name = "github_detail"
    mock_config: Final = {"owner": "zulip", "repo": "zulip"}
    empty_config: Final = {"owner": "", "repo": ""}

    # Overrides default test_bot_usage().
    @override
    def test_bot_usage(self) -> None:
        bot = get_bot_message_handler(self.bot_name)
        bot_handler = StubBotHandler()

        with self.mock_config_info(self.mock_config):
            bot.initialize(bot_handler)

        self.assertIn("displays details on github issues", bot.usage())

    # Override default function in BotTestCase
    @override
    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info(self.mock_config):
            self.verify_reply("", "Failed to find any issue or PR.")

    def test_issue(self) -> None:
        request = "zulip/zulip#5365"
        bot_response = (
            "**[zulip/zulip#5365](https://github.com/zulip/zulip/issues/5365)"
            " - frontend: Enable hot-reloading of CSS in development**\n"
            "Created by **[timabbott](https://github.com/timabbott)**\n"
            "Status - **Open**\n"
            "```quote\n"
            "There's strong interest among folks working on the frontend in being "
            "able to use the hot-reloading feature of webpack for managing our CSS.\r\n\r\n"
            "In order to do this, step 1 is to move our CSS minification pipeline "
            "from django-pipeline to Webpack.  \n```"
        )

        with self.mock_http_conversation("test_issue"):
            with self.mock_config_info(self.mock_config):
                self.verify_reply(request, bot_response)

    def test_pull_request(self) -> None:
        request = "zulip/zulip#5345"
        bot_response = (
            "**[zulip/zulip#5345](https://github.com/zulip/zulip/pull/5345)"
            " - [WIP] modal: Replace bootstrap modal with custom modal class**\n"
            "Created by **[jackrzhang](https://github.com/jackrzhang)**\n"
            "Status - **Open**\n```quote\nAn interaction bug (#4811)  "
            "between our settings UI and the bootstrap modals breaks hotkey "
            "support for `Esc` when multiple modals are open.\r\n\r\ntodo:\r\n[x]"
            " Create `Modal` class in `modal.js` (drafted by @brockwhittaker)\r\n[x]"
            " Reimplement change_email_modal utilizing `Modal` class\r\n[] Dump "
            "using bootstrap for the account settings modal and all other modals,"
            " replace with `Modal` class\r\n[] Add hotkey support for closing the"
            " top modal for `Esc`\r\n\r\nThis should also be a helpful step in"
            " removing dependencies from Bootstrap.\n```"
        )
        with self.mock_http_conversation("test_pull"):
            with self.mock_config_info(self.mock_config):
                self.verify_reply(request, bot_response)

    def test_404(self) -> None:
        request = "zulip/zulip#0"
        bot_response = "Failed to find issue/pr: zulip/zulip#0"
        with self.mock_http_conversation("test_404"):
            with self.mock_config_info(self.mock_config):
                self.verify_reply(request, bot_response)

    def test_exception(self) -> None:
        request = "zulip/zulip#0"
        bot_response = "Failed to find issue/pr: zulip/zulip#0"
        with self.mock_request_exception():
            with self.mock_config_info(self.mock_config):
                self.verify_reply(request, bot_response)

    def test_random_text(self) -> None:
        request = "some random text"
        bot_response = "Failed to find any issue or PR."
        with self.mock_config_info(self.mock_config):
            self.verify_reply(request, bot_response)

    def test_help_text(self) -> None:
        request = "help"
        bot_response = (
            "This plugin displays details on github issues and pull requests. "
            "To reference an issue or pull request usename mention the bot then "
            "anytime in the message type its id, for example:\n@**Github detail** "
            "#3212 zulip#3212 zulip/zulip#3212\nThe default owner is zulip and "
            "the default repo is zulip."
        )

        with self.mock_config_info(self.mock_config):
            self.verify_reply(request, bot_response)

    def test_too_many_request(self) -> None:
        request = (
            "zulip/zulip#1 zulip/zulip#1 zulip/zulip#1 zulip/zulip#1 "
            "zulip/zulip#1 zulip/zulip#1 zulip/zulip#1 zulip/zulip#1"
        )
        bot_response = "Please ask for <=5 links in any one request"

        with self.mock_config_info(self.mock_config):
            self.verify_reply(request, bot_response)

    def test_owner_and_repo_not_specified(self) -> None:
        request = "/#1"
        bot_response = "Failed to detect owner and repository name."
        with self.mock_config_info(self.empty_config):
            self.verify_reply(request, bot_response)

    def test_owner_and_repo_specified_in_config_file(self) -> None:
        request = "/#5345"
        bot_response = (
            "**[zulip/zulip#5345](https://github.com/zulip/zulip/pull/5345)"
            " - [WIP] modal: Replace bootstrap modal with custom modal class**\n"
            "Created by **[jackrzhang](https://github.com/jackrzhang)**\n"
            "Status - **Open**\n```quote\nAn interaction bug (#4811)  "
            "between our settings UI and the bootstrap modals breaks hotkey "
            "support for `Esc` when multiple modals are open.\r\n\r\ntodo:\r\n[x]"
            " Create `Modal` class in `modal.js` (drafted by @brockwhittaker)\r\n[x]"
            " Reimplement change_email_modal utilizing `Modal` class\r\n[] Dump "
            "using bootstrap for the account settings modal and all other modals,"
            " replace with `Modal` class\r\n[] Add hotkey support for closing the"
            " top modal for `Esc`\r\n\r\nThis should also be a helpful step in"
            " removing dependencies from Bootstrap.\n```"
        )
        with self.mock_http_conversation("test_pull"):
            with self.mock_config_info(self.mock_config):
                self.verify_reply(request, bot_response)

    def test_owner_and_repo_specified_in_message(self) -> None:
        request = "zulip/zulip#5345"
        bot_response = (
            "**[zulip/zulip#5345](https://github.com/zulip/zulip/pull/5345)"
            " - [WIP] modal: Replace bootstrap modal with custom modal class**\n"
            "Created by **[jackrzhang](https://github.com/jackrzhang)**\n"
            "Status - **Open**\n```quote\nAn interaction bug (#4811)  "
            "between our settings UI and the bootstrap modals breaks hotkey "
            "support for `Esc` when multiple modals are open.\r\n\r\ntodo:\r\n[x]"
            " Create `Modal` class in `modal.js` (drafted by @brockwhittaker)\r\n[x]"
            " Reimplement change_email_modal utilizing `Modal` class\r\n[] Dump "
            "using bootstrap for the account settings modal and all other modals,"
            " replace with `Modal` class\r\n[] Add hotkey support for closing the"
            " top modal for `Esc`\r\n\r\nThis should also be a helpful step in"
            " removing dependencies from Bootstrap.\n```"
        )
        with self.mock_http_conversation("test_pull"):
            with self.mock_config_info(self.empty_config):
                self.verify_reply(request, bot_response)

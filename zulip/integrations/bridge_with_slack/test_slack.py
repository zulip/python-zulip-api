import importlib.machinery
import importlib.util
import os
import sys
from typing import Any, Dict
from unittest import TestCase, mock

from typing_extensions import override

if "slack_sdk" not in sys.modules:
    try:
        import slack_sdk  # noqa: F401
    except ImportError:  # pragma: no cover
        sys.modules["slack_sdk"] = mock.MagicMock()
        sys.modules["slack_sdk.web"] = mock.MagicMock()
        sys.modules["slack_sdk.web.client"] = mock.MagicMock()

bridge_dir = os.path.dirname(__file__)
bridge_path = os.path.join(bridge_dir, "run-slack-bridge")

sys.path.insert(0, bridge_dir)
sys.path.insert(0, os.path.abspath(os.path.join(bridge_dir, "..", "..")))

loader = importlib.machinery.SourceFileLoader("run_slack_bridge", bridge_path)
spec = importlib.util.spec_from_loader("run_slack_bridge", loader)
assert spec is not None
run_slack_bridge = importlib.util.module_from_spec(spec)
sys.modules["run_slack_bridge"] = run_slack_bridge
loader.exec_module(run_slack_bridge)

SlackBridge = run_slack_bridge.SlackBridge
get_slack_channel_for_zulip_message = run_slack_bridge.get_slack_channel_for_zulip_message

check_token_access = run_slack_bridge.check_token_access

from slack_markdown import slack_to_zulip_markdown, zulip_to_slack_markdown


class SlackMarkdownTranslationTestCase(TestCase):
    def test_zulip_to_slack_bold(self) -> None:
        self.assertEqual(zulip_to_slack_markdown("This is **bold** text."), "This is *bold* text.")
        self.assertEqual(
            zulip_to_slack_markdown("**first** and **second**"), "*first* and *second*"
        )

    def test_zulip_to_slack_italic(self) -> None:
        self.assertEqual(
            zulip_to_slack_markdown("This is *italic* text."), "This is _italic_ text."
        )

    def test_zulip_to_slack_bold_and_italic(self) -> None:
        self.assertEqual(
            zulip_to_slack_markdown("Here is **bold** and *italic* together."),
            "Here is *bold* and _italic_ together.",
        )

    def test_zulip_to_slack_strikethrough(self) -> None:
        self.assertEqual(
            zulip_to_slack_markdown("This is ~~deleted~~ text."), "This is ~deleted~ text."
        )

    def test_zulip_to_slack_links(self) -> None:
        self.assertEqual(
            zulip_to_slack_markdown("Visit [Zulip](https://zulip.com) for details."),
            "Visit <https://zulip.com|Zulip> for details.",
        )
        self.assertEqual(
            zulip_to_slack_markdown("[Docs](https://zulip.com/api?a=1&b=2)"),
            "<https://zulip.com/api?a=1&b=2|Docs>",
        )

    def test_zulip_to_slack_mentions(self) -> None:
        self.assertEqual(
            zulip_to_slack_markdown("Hello @**Alice Smith**!"), "Hello <@Alice Smith>!"
        )
        self.assertEqual(
            zulip_to_slack_markdown("Ping @**Bob Jones|1234** for review."),
            "Ping <@Bob Jones> for review.",
        )
        self.assertEqual(
            zulip_to_slack_markdown("Silent notification @_**Charlie** here."),
            "Silent notification <@Charlie> here.",
        )
        self.assertEqual(zulip_to_slack_markdown("Hi @developer!"), "Hi <@developer>!")

    def test_zulip_to_slack_wildcard_mentions(self) -> None:
        self.assertEqual(zulip_to_slack_markdown("Attention @**all**!"), "Attention <!everyone>!")
        self.assertEqual(
            zulip_to_slack_markdown("Attention @**everyone**!"), "Attention <!everyone>!"
        )
        self.assertEqual(
            zulip_to_slack_markdown("Notice for @**stream**."), "Notice for <!channel>."
        )
        self.assertEqual(
            zulip_to_slack_markdown("Notice for @**channel**."), "Notice for <!channel>."
        )
        self.assertEqual(zulip_to_slack_markdown("Paging @**here**!"), "Paging <!here>!")

    def test_zulip_to_slack_stream_links(self) -> None:
        self.assertEqual(zulip_to_slack_markdown("Join #**general**."), "Join #general.")
        self.assertEqual(
            zulip_to_slack_markdown("Check #**design>redesign** discussion."),
            "Check #design discussion.",
        )

    def test_zulip_to_slack_code_protection(self) -> None:
        self.assertEqual(
            zulip_to_slack_markdown("Use `**not bold**` inline."), "Use `**not bold**` inline."
        )
        code_block = "```python\nprint('**hello**')\n[label](url)\n```"
        self.assertEqual(
            zulip_to_slack_markdown(f"Header **bold**\n{code_block}\nFooter **bold**"),
            f"Header *bold*\n{code_block}\nFooter *bold*",
        )

    def test_slack_to_zulip_bold(self) -> None:
        self.assertEqual(slack_to_zulip_markdown("This is *bold* text."), "This is **bold** text.")
        self.assertEqual(
            slack_to_zulip_markdown("*first* and *second*"), "**first** and **second**"
        )

    def test_slack_to_zulip_strikethrough(self) -> None:
        self.assertEqual(
            slack_to_zulip_markdown("This is ~deleted~ text."), "This is ~~deleted~~ text."
        )

    def test_slack_to_zulip_links(self) -> None:
        self.assertEqual(
            slack_to_zulip_markdown("Visit <https://slack.com|Slack> today."),
            "Visit [Slack](https://slack.com) today.",
        )
        self.assertEqual(
            slack_to_zulip_markdown("Bare URL: <https://zulip.com>"), "Bare URL: https://zulip.com"
        )

    def test_slack_to_zulip_mentions(self) -> None:
        self.assertEqual(slack_to_zulip_markdown("Hello <@U12345|Alice>!"), "Hello @**Alice**!")
        self.assertEqual(slack_to_zulip_markdown("Hello <@U12345>!"), "Hello @**U12345**!")
        self.assertEqual(slack_to_zulip_markdown("Hello <@alice>!"), "Hello @**alice**!")

    def test_slack_to_zulip_channel_mentions(self) -> None:
        self.assertEqual(slack_to_zulip_markdown("Join <#C12345|general>."), "Join #**general**.")
        self.assertEqual(slack_to_zulip_markdown("Join <#C12345>."), "Join #**C12345**.")

    def test_slack_to_zulip_wildcards(self) -> None:
        self.assertEqual(
            slack_to_zulip_markdown("Attention <!everyone>!"), "Attention @**everyone**!"
        )
        self.assertEqual(
            slack_to_zulip_markdown("Notice for <!channel>."), "Notice for @**channel**."
        )
        self.assertEqual(slack_to_zulip_markdown("Paging <!here>!"), "Paging @**here**!")

    def test_slack_to_zulip_code_protection(self) -> None:
        self.assertEqual(
            slack_to_zulip_markdown("Use `*not bold*` inline."), "Use `*not bold*` inline."
        )
        code_block = "```\n*not bold*\n<https://example.com|link>\n```"
        self.assertEqual(
            slack_to_zulip_markdown(f"Header *bold*\n{code_block}\nFooter *bold*"),
            f"Header **bold**\n{code_block}\nFooter **bold**",
        )


class SlackBridgeTestCase(TestCase):
    @override
    def setUp(self) -> None:
        self.base_config: Dict[str, Any] = {
            "zulip": {
                "email": "slack-bot@zulip.org",
                "api_key": "some_zulip_api_key",
                "site": "https://chat.zulip.org",
            },
            "slack": {
                "username": "slack_bridge_bot",
                "token": "xoxb-test-token",
            },
            "channel_mapping": {
                "C12345": {
                    "channel": "general",
                    "topic": "slack-topic",
                }
            },
        }

    @mock.patch.object(run_slack_bridge, "WebClient")
    @mock.patch.object(run_slack_bridge.zulip, "Client")
    def test_wrap_slack_mention_with_bracket_translates_markdown(
        self, mock_zulip_client: mock.MagicMock, mock_web_client: mock.MagicMock
    ) -> None:
        bridge = SlackBridge(self.base_config)
        msg: Dict[str, Any] = {
            "content": "Hello **world**, check [Zulip](https://zulip.com) and @**Alice**!"
        }
        bridge.wrap_slack_mention_with_bracket(msg)
        self.assertEqual(
            msg["content"],
            "Hello *world*, check <https://zulip.com|Zulip> and <@Alice>!",
        )

    @mock.patch.object(run_slack_bridge, "WebClient")
    @mock.patch.object(run_slack_bridge.zulip, "Client")
    def test_zulip_to_slack_post_message_with_markdown_translation(
        self, mock_zulip_client: mock.MagicMock, mock_web_client: mock.MagicMock
    ) -> None:
        mock_slack = mock_web_client.return_value
        bridge = SlackBridge(self.base_config)
        handler = bridge.zulip_to_slack()

        msg = {
            "type": "stream",
            "display_recipient": "general",
            "subject": "slack-topic",
            "sender_email": "developer@zulip.org",
            "sender_full_name": "Dev User",
            "content": "Check **important** update: [PR](https://github.com/zulip) for @**reviewer**",
        }
        handler(msg)

        mock_slack.chat_postMessage.assert_called_once_with(
            channel="C12345",
            text="<Dev User> Check *important* update: <https://github.com/zulip|PR> for <@reviewer>",
        )

    def test_get_slack_channel_for_zulip_message(self) -> None:
        zulip_to_slack_map = {
            ("general", "slack-topic"): "C12345",
        }
        bot_email = "slack-bot@zulip.org"

        # Valid matching stream message
        msg_valid = {
            "type": "stream",
            "display_recipient": "general",
            "subject": "slack-topic",
            "sender_email": "user@zulip.org",
        }
        self.assertEqual(
            get_slack_channel_for_zulip_message(msg_valid, zulip_to_slack_map, bot_email),
            "C12345",
        )

        # Message from bridge bot itself (prevent loop)
        msg_bot = dict(msg_valid, sender_email=bot_email)
        self.assertIsNone(
            get_slack_channel_for_zulip_message(msg_bot, zulip_to_slack_map, bot_email)
        )

        # Message with non-matching stream or topic
        msg_other = dict(msg_valid, subject="other-topic")
        self.assertIsNone(
            get_slack_channel_for_zulip_message(msg_other, zulip_to_slack_map, bot_email)
        )

    def test_check_token_access(self) -> None:
        # Valid bot token should succeed without error
        check_token_access("xoxb-valid-bot-token")

        # User token should print warning and exit
        with self.assertRaises(SystemExit):
            check_token_access("xoxp-user-token")

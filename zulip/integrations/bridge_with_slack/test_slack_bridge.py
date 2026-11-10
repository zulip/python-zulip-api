import importlib.machinery
import importlib.util
import os
import sys
from typing import Any, Dict
from unittest import TestCase, mock

import pytest
from typing_extensions import override

pytest.importorskip("slack_sdk")

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
            "channel_mapping": {},
        }

    @mock.patch.object(run_slack_bridge, "WebClient")
    @mock.patch.object(run_slack_bridge.zulip, "Client")
    def test_static_topic_mapping(
        self, mock_zulip_client: mock.MagicMock, mock_web_client: mock.MagicMock
    ) -> None:
        config = dict(self.base_config)
        config["channel_mapping"] = {
            "C12345": {
                "channel": "general",
                "topic": "custom-topic",
            }
        }

        bridge = SlackBridge(config)
        self.assertEqual(bridge.zulip_to_slack_map, {("general", "custom-topic"): "C12345"})
        # conversations_info should not be called when topic has no placeholder
        mock_web_client.return_value.conversations_info.assert_not_called()

    @mock.patch.object(run_slack_bridge, "WebClient")
    @mock.patch.object(run_slack_bridge.zulip, "Client")
    def test_channel_name_topic_substitution(
        self, mock_zulip_client: mock.MagicMock, mock_web_client: mock.MagicMock
    ) -> None:
        mock_slack = mock_web_client.return_value
        mock_slack.conversations_info.return_value = {
            "ok": True,
            "channel": {"name": "dev-announcements"},
        }

        config = dict(self.base_config)
        config["channel_mapping"] = {
            "C99999": {
                "channel": "slack-feed",
                "topic": "{channel_name}",
            }
        }

        bridge = SlackBridge(config)
        mock_slack.conversations_info.assert_called_once_with(channel="C99999")
        self.assertEqual(bridge.zulip_to_slack_map, {("slack-feed", "dev-announcements"): "C99999"})

    @mock.patch.object(run_slack_bridge, "WebClient")
    @mock.patch.object(run_slack_bridge.zulip, "Client")
    def test_channel_name_topic_prefix_template(
        self, mock_zulip_client: mock.MagicMock, mock_web_client: mock.MagicMock
    ) -> None:
        mock_slack = mock_web_client.return_value
        mock_slack.conversations_info.return_value = {
            "ok": True,
            "channel": {"name": "general"},
        }

        config = dict(self.base_config)
        config["channel_mapping"] = {
            "C55555": {
                "channel": "slack-sync",
                "topic": "slack: {channel_name}",
            }
        }

        bridge = SlackBridge(config)
        mock_slack.conversations_info.assert_called_once_with(channel="C55555")
        self.assertEqual(bridge.zulip_to_slack_map, {("slack-sync", "slack: general"): "C55555"})

    @mock.patch.object(run_slack_bridge, "WebClient")
    @mock.patch.object(run_slack_bridge.zulip, "Client")
    def test_topic_omitted_defaults_to_channel_name(
        self, mock_zulip_client: mock.MagicMock, mock_web_client: mock.MagicMock
    ) -> None:
        mock_slack = mock_web_client.return_value
        mock_slack.conversations_info.return_value = {
            "ok": True,
            "channel": {"name": "random"},
        }

        config = dict(self.base_config)
        config["channel_mapping"] = {
            "C88888": {
                "channel": "random-zulip",
            }
        }

        bridge = SlackBridge(config)
        mock_slack.conversations_info.assert_called_once_with(channel="C88888")
        self.assertEqual(bridge.zulip_to_slack_map, {("random-zulip", "random"): "C88888"})

    @mock.patch.object(run_slack_bridge, "WebClient")
    @mock.patch.object(run_slack_bridge.zulip, "Client")
    def test_channel_name_resolution_failure_fallback(
        self, mock_zulip_client: mock.MagicMock, mock_web_client: mock.MagicMock
    ) -> None:
        mock_slack = mock_web_client.return_value
        # Simulate API error or exception
        mock_slack.conversations_info.side_effect = Exception("Slack API rate limited")

        config = dict(self.base_config)
        config["channel_mapping"] = {
            "C40404": {
                "channel": "fallback-test",
                "topic": "{channel_name}",
            }
        }

        bridge = SlackBridge(config)
        # Should gracefully fall back to channel ID
        self.assertEqual(bridge.zulip_to_slack_map, {("fallback-test", "C40404"): "C40404"})

    def test_get_slack_channel_for_zulip_message(self) -> None:
        zulip_to_slack_map = {
            ("general", "slack-topic"): "C11111",
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
            "C11111",
        )

        # Message from bridge bot itself (prevent loop)
        msg_bot = dict(msg_valid, sender_email=bot_email)
        self.assertIsNone(
            get_slack_channel_for_zulip_message(msg_bot, zulip_to_slack_map, bot_email)
        )

        # Message from private type (not stream)
        msg_private = dict(msg_valid, type="private")
        self.assertIsNone(
            get_slack_channel_for_zulip_message(msg_private, zulip_to_slack_map, bot_email)
        )

        # Message with non-matching topic
        msg_other_topic = dict(msg_valid, subject="unbridged-topic")
        self.assertIsNone(
            get_slack_channel_for_zulip_message(msg_other_topic, zulip_to_slack_map, bot_email)
        )

    @mock.patch.object(run_slack_bridge, "WebClient")
    @mock.patch.object(run_slack_bridge.zulip, "Client")
    def test_zulip_to_slack_post_message(
        self, mock_zulip_client: mock.MagicMock, mock_web_client: mock.MagicMock
    ) -> None:
        mock_slack = mock_web_client.return_value
        config = dict(self.base_config)
        config["channel_mapping"] = {
            "C12345": {
                "channel": "design",
                "topic": "ui-ux",
            }
        }

        bridge = SlackBridge(config)
        handler = bridge.zulip_to_slack()

        msg = {
            "type": "stream",
            "display_recipient": "design",
            "subject": "ui-ux",
            "sender_email": "designer@zulip.org",
            "sender_full_name": "Alice Smith",
            "content": "Hello @everyone",
        }
        handler(msg)

        mock_slack.chat_postMessage.assert_called_once_with(
            channel="C12345",
            text="<Alice Smith> Hello <@everyone>",
        )

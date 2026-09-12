import io
from typing import Any, List
from unittest import TestCase
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from typing_extensions import override

from integrations.clickup import zulip_clickup
from integrations.clickup.zulip_clickup import ClickUpAPIHandler

SCRIPT_PATH = "integrations.clickup.zulip_clickup"

MOCK_WEBHOOK_URL = (
    "https://YourZulipApp.com/api/v1/external/clickup?api_key=TJ9DnIiNqt51bpfyPll5n2uT4iYxMBW9"
)

MOCK_API_KEY = "pk_" + "1" * 32
CLICKUP_TEAM_ID = "teamid123"

MOCK_CREATED_WEBHOOK_ID = "13-13-13-13-1313-13"
MOCK_DELETE_WEBHOOK_ID = "12-12-12-12-12"

REQUIRED_ARGS = [
    "zulip_clickup.py",
    "--clickup-team-id",
    CLICKUP_TEAM_ID,
    "--clickup-api-key",
    MOCK_API_KEY,
    "--zulip-webhook-url",
    MOCK_WEBHOOK_URL,
]


def make_urlopen_response(status: int, body: bytes) -> MagicMock:
    """Build a mock that behaves like the context manager urlopen() returns."""
    response = MagicMock()
    response.status = status
    response.read.return_value = body
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class ArgumentParsingTest(TestCase):
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch(SCRIPT_PATH + ".run")
    @patch("sys.argv", REQUIRED_ARGS)
    def test_valid_arguments(self, mock_run: MagicMock, mock_stdout: io.StringIO) -> None:
        zulip_clickup.main()
        self.assertRegex(mock_stdout.getvalue(), r"Running Zulip Clickup Integration...")
        mock_run.assert_called_once_with(CLICKUP_TEAM_ID, MOCK_API_KEY, MOCK_WEBHOOK_URL, False)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch(SCRIPT_PATH + ".run")
    @patch("sys.argv", [*REQUIRED_ARGS, "--replace-existing"])
    def test_replace_existing_flag(self, mock_run: MagicMock, mock_stdout: io.StringIO) -> None:
        zulip_clickup.main()
        self.assertRegex(mock_stdout.getvalue(), r"Running Zulip Clickup Integration...")
        mock_run.assert_called_once_with(CLICKUP_TEAM_ID, MOCK_API_KEY, MOCK_WEBHOOK_URL, True)

    @patch("sys.stderr", new_callable=io.StringIO)
    @patch("sys.argv", ["zulip_clickup.py"])
    def test_missing_arguments(self, mock_stderr: io.StringIO) -> None:
        with self.assertRaises(SystemExit) as cm:
            zulip_clickup.main()
        self.assertEqual(cm.exception.code, 2)
        self.assertRegex(
            mock_stderr.getvalue(),
            r"the following arguments are required: "
            r"--clickup-team-id, --clickup-api-key, --zulip-webhook-url",
        )


class EventSelectionTest(TestCase):
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["1"])
    def test_select_event_group(self, mock_input: MagicMock, mock_stdout: io.StringIO) -> None:
        events = zulip_clickup.query_for_notification_events()
        menu = mock_stdout.getvalue()
        for expected in (
            "1 = task",
            "2 = list",
            "3 = folder",
            "4 = space",
            "5 = goal",
            "6 = target",
        ):
            self.assertIn(expected, menu)
        self.assertEqual(events, ["taskCreated", "taskUpdated", "taskDeleted"])

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["1,2,3"])
    def test_select_multiple_event_groups(
        self, mock_input: MagicMock, mock_stdout: io.StringIO
    ) -> None:
        events = zulip_clickup.query_for_notification_events()
        self.assertEqual(
            events,
            [
                "taskCreated",
                "taskUpdated",
                "taskDeleted",
                "listCreated",
                "listUpdated",
                "listDeleted",
                "folderCreated",
                "folderUpdated",
                "folderDeleted",
            ],
        )

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["2,,5"])
    def test_select_ignores_blank_tokens(
        self, mock_input: MagicMock, mock_stdout: io.StringIO
    ) -> None:
        events = zulip_clickup.query_for_notification_events()
        self.assertEqual(
            events,
            [
                "listCreated",
                "listUpdated",
                "listDeleted",
                "goalCreated",
                "goalUpdated",
                "goalDeleted",
            ],
        )

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["*"])
    def test_select_all_events(self, mock_input: MagicMock, mock_stdout: io.StringIO) -> None:
        events = zulip_clickup.query_for_notification_events()
        expected = [event for group in zulip_clickup.EVENT_CHOICES.values() for event in group]
        self.assertEqual(events, expected)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["9", "1"])
    def test_invalid_then_valid_input(
        self, mock_input: MagicMock, mock_stdout: io.StringIO
    ) -> None:
        events = zulip_clickup.query_for_notification_events()
        self.assertEqual(events, ["taskCreated", "taskUpdated", "taskDeleted"])
        self.assertRegex(
            mock_stdout.getvalue(),
            r"Please enter a valid set of options",
        )


class ClickUpAPIHandlerTest(TestCase):
    @override
    def setUp(self) -> None:
        self.handler = ClickUpAPIHandler(MOCK_API_KEY, CLICKUP_TEAM_ID)

    def test_constructor_and_endpoints(self) -> None:
        self.assertEqual(self.handler.api_key, MOCK_API_KEY)
        self.assertEqual(self.handler.team_id, CLICKUP_TEAM_ID)
        self.assertEqual(set(self.handler.ENDPOINTS), {"team", "webhook"})

    @patch(SCRIPT_PATH + ".urlopen", return_value=make_urlopen_response(200, b'{"id": "abc"}'))
    def test_valid_request(self, mock_urlopen: MagicMock) -> None:
        data = self.handler.make_clickup_request(
            self.handler.ENDPOINTS["team"],
            {"endpoint": "u", "events": ["taskCreated"]},
            "POST",
        )
        self.assertEqual(data, {"id": "abc"})

    def test_get_and_delete_send_no_body(self) -> None:
        captured: List[Any] = []

        def fake_urlopen(req: Any) -> MagicMock:
            captured.append(req)
            return make_urlopen_response(200, b"{}")

        with patch(SCRIPT_PATH + ".urlopen", side_effect=fake_urlopen):
            self.handler.make_clickup_request(self.handler.ENDPOINTS["team"], {}, "GET")
            self.handler.make_clickup_request(
                self.handler.ENDPOINTS["team"], {"endpoint": "u", "events": ["x"]}, "POST"
            )
            self.handler.make_clickup_request("webhook/1", {}, "DELETE")

        get_req, post_req, delete_req = captured
        self.assertIsNone(get_req.data)
        self.assertIsNotNone(post_req.data)
        self.assertIsNone(delete_req.data)

    def test_authorization_header_is_raw_token(self) -> None:
        captured: List[Any] = []

        def fake_urlopen(req: Any) -> MagicMock:
            captured.append(req)
            return make_urlopen_response(200, b"{}")

        with patch(SCRIPT_PATH + ".urlopen", side_effect=fake_urlopen):
            self.handler.make_clickup_request(self.handler.ENDPOINTS["team"], {}, "GET")
        self.assertEqual(captured[0].headers["Authorization"], MOCK_API_KEY)

    def test_response_with_httperror(self) -> None:
        err = HTTPError(MOCK_WEBHOOK_URL, 403, "Forbidden", {}, None)  # type: ignore[arg-type]
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            with patch(SCRIPT_PATH + ".urlopen", side_effect=err):
                data = self.handler.make_clickup_request(self.handler.ENDPOINTS["team"], {}, "GET")
        self.assertIsNone(data)
        self.assertRegex(mock_stdout.getvalue(), r"HTTPError occurred: 403")

    def test_response_with_urlerror(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            with patch(SCRIPT_PATH + ".urlopen", side_effect=URLError("network down")):
                data = self.handler.make_clickup_request(self.handler.ENDPOINTS["team"], {}, "GET")
        self.assertIsNone(data)
        self.assertRegex(mock_stdout.getvalue(), r"Network error occurred")

    @patch(
        SCRIPT_PATH + ".urlopen",
        return_value=make_urlopen_response(200, b"<html>Service Unavailable</html>"),
    )
    def test_response_with_non_json_body(self, mock_urlopen: MagicMock) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            data = self.handler.make_clickup_request(self.handler.ENDPOINTS["team"], {}, "GET")
        self.assertIsNone(data)
        self.assertRegex(mock_stdout.getvalue(), r"Could not parse ClickUp's response")

    @patch.object(
        ClickUpAPIHandler, "make_clickup_request", return_value={"id": MOCK_CREATED_WEBHOOK_ID}
    )
    def test_create_webhook(self, mock_request: MagicMock) -> None:
        data = self.handler.create_webhook(MOCK_WEBHOOK_URL, ["taskCreated"])
        self.assertEqual(data["id"], MOCK_CREATED_WEBHOOK_ID)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch.object(ClickUpAPIHandler, "make_clickup_request", return_value=None)
    def test_create_webhook_with_failure(
        self, mock_request: MagicMock, mock_stdout: io.StringIO
    ) -> None:
        with self.assertRaises(SystemExit) as cm:
            self.handler.create_webhook(MOCK_WEBHOOK_URL, ["taskCreated"])
        self.assertEqual(cm.exception.code, 1)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch.object(ClickUpAPIHandler, "make_clickup_request", return_value=None)
    def test_get_webhooks_with_failure(
        self, mock_request: MagicMock, mock_stdout: io.StringIO
    ) -> None:
        with self.assertRaises(SystemExit) as cm:
            self.handler.get_webhooks()
        self.assertEqual(cm.exception.code, 1)


class DeleteOldWebhooksTest(TestCase):
    @patch.object(ClickUpAPIHandler, "delete_webhook")
    @patch.object(ClickUpAPIHandler, "get_webhooks")
    def test_matches_exact_url_only(
        self, mock_get_webhooks: MagicMock, mock_delete_webhook: MagicMock
    ) -> None:
        target = MOCK_WEBHOOK_URL
        same_host_other_bot = "https://YourZulipApp.com/api/v1/external/clickup?api_key=SOMEOTHERBOTKEY0000000000000000"
        mock_get_webhooks.return_value = {
            "webhooks": [
                {"id": "match", "endpoint": target},
                {"id": "other-bot", "endpoint": same_host_other_bot},
            ]
        }
        deleted: List[str] = []
        mock_delete_webhook.side_effect = deleted.append

        handler = ClickUpAPIHandler(MOCK_API_KEY, CLICKUP_TEAM_ID)
        zulip_clickup.delete_old_webhooks(target, handler)

        self.assertEqual(deleted, ["match"])


class RunTest(TestCase):
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch(SCRIPT_PATH + ".query_for_notification_events", return_value=["taskCreated"])
    @patch(SCRIPT_PATH + ".delete_old_webhooks")
    @patch.object(ClickUpAPIHandler, "create_webhook", return_value={"id": MOCK_CREATED_WEBHOOK_ID})
    def test_run_without_replace_skips_delete(
        self,
        mock_create: MagicMock,
        mock_delete_old: MagicMock,
        mock_events: MagicMock,
        mock_stdout: io.StringIO,
    ) -> None:
        with self.assertRaises(SystemExit) as cm:
            zulip_clickup.run(CLICKUP_TEAM_ID, MOCK_API_KEY, MOCK_WEBHOOK_URL, False)
        self.assertEqual(cm.exception.code, 0)
        mock_delete_old.assert_not_called()
        mock_create.assert_called_once()
        self.assertRegex(mock_stdout.getvalue(), r"SUCCESS: Completed integrating")

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch(SCRIPT_PATH + ".query_for_notification_events", return_value=["taskCreated"])
    @patch(SCRIPT_PATH + ".delete_old_webhooks")
    @patch.object(ClickUpAPIHandler, "create_webhook", return_value={"id": MOCK_CREATED_WEBHOOK_ID})
    def test_run_with_replace_calls_delete(
        self,
        mock_create: MagicMock,
        mock_delete_old: MagicMock,
        mock_events: MagicMock,
        mock_stdout: io.StringIO,
    ) -> None:
        with self.assertRaises(SystemExit) as cm:
            zulip_clickup.run(CLICKUP_TEAM_ID, MOCK_API_KEY, MOCK_WEBHOOK_URL, True)
        self.assertEqual(cm.exception.code, 0)
        mock_delete_old.assert_called_once()
        self.assertEqual(mock_delete_old.call_args[0][0], MOCK_WEBHOOK_URL)
        mock_create.assert_called_once()

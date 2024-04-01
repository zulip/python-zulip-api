import io
import re
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union
from unittest import TestCase
from unittest.mock import DEFAULT, patch

from integrations.clickup import zulip_clickup
from integrations.clickup.zulip_clickup import ClickUpAPIHandler

MOCK_WEBHOOK_URL = (
    "https://YourZulipApp.com/api/v1/external/clickup?api_key=TJ9DnIiNqt51bpfyPll5n2uT4iYxMBW9"
)

MOCK_AUTH_CODE = "332KKA3321NNAK3MADS"
MOCK_AUTH_CODE_URL = f"https://YourZulipApp.com/?code={MOCK_AUTH_CODE}"
MOCK_API_KEY = "X" * 32

SCRIPT_PATH = "integrations.clickup.zulip_clickup"

MOCK_CREATED_WEBHOOK_ID = "13-13-13-13-1313-13"
MOCK_DELETE_WEBHOOK_ID = "12-12-12-12-12"
MOCK_GET_WEBHOOK_IDS = {"endpoint": MOCK_WEBHOOK_URL, "id": MOCK_DELETE_WEBHOOK_ID}

CLICKUP_TEAM_ID = "teamid123"
CLICKUP_CLIENT_ID = "clientid321"
CLICKUP_CLIENT_SECRET = "clientsecret322"  # noqa: S105


def make_clickup_request_side_effect(
    path: str, query: Dict[str, Union[str, List[str]]], method: str
) -> Optional[Dict[str, Any]]:
    clickup_api = ClickUpAPIHandler(CLICKUP_CLIENT_ID, CLICKUP_CLIENT_SECRET, CLICKUP_TEAM_ID)
    api_data_mapper: Dict[str, Dict[str, Dict[str, Any]]] = {  # path -> method -> response
        clickup_api.ENDPOINTS["oauth"]: {
            "POST": {"access_token": MOCK_API_KEY},
        },
        clickup_api.ENDPOINTS["team"]: {
            "POST": {"id": MOCK_CREATED_WEBHOOK_ID},
            "GET": {"webhooks": [MOCK_GET_WEBHOOK_IDS]},
        },
        clickup_api.ENDPOINTS["webhook"].format(webhook_id=MOCK_DELETE_WEBHOOK_ID): {"DELETE": {}},
    }
    return api_data_mapper.get(path, {}).get(method, DEFAULT)


def mock_script_args(selected_events: str = "1,2,3,4,5") -> Callable[[Any], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            mock_user_inputs = [MOCK_AUTH_CODE_URL, selected_events]
            with patch(
                "sys.argv",
                [
                    "zulip_clickup.py",
                    "--clickup-team-id",
                    CLICKUP_TEAM_ID,
                    "--clickup-client-id",
                    CLICKUP_CLIENT_ID,
                    "--clickup-client-secret",
                    CLICKUP_CLIENT_SECRET,
                    "--zulip-webhook-url",
                    MOCK_WEBHOOK_URL,
                ],
            ), patch("sys.exit"), patch("builtins.input", side_effect=mock_user_inputs), patch(
                SCRIPT_PATH + ".ClickUpAPIHandler.make_clickup_request",
                side_effect=make_clickup_request_side_effect,
            ):
                result = func(*args, **kwargs)

            return result

        return wrapper

    return decorator


class ZulipClickUpScriptTest(TestCase):
    @mock_script_args()
    def test_valid_arguments(self) -> None:
        with patch(SCRIPT_PATH + ".run") as mock_run, patch(
            "sys.stdout", new=io.StringIO()
        ) as mock_stdout:
            zulip_clickup.main()
            self.assertRegex(mock_stdout.getvalue(), r"Running Zulip Clickup Integration...")
            mock_run.assert_called_once_with(
                CLICKUP_CLIENT_ID, CLICKUP_CLIENT_SECRET, CLICKUP_TEAM_ID, MOCK_WEBHOOK_URL
            )

    def test_missing_arguments(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            with patch("sys.stderr", new=io.StringIO()) as mock_stderr:
                zulip_clickup.main()
        self.assertEqual(cm.exception.code, 2)
        self.assertRegex(
            mock_stderr.getvalue(),
            r"""the following arguments are required: --clickup-team-id, --clickup-client-id, --clickup-client-secret, --zulip-webhook-url\n""",
        )

    @mock_script_args()
    def test_redirect_to_auth_page(self) -> None:
        with patch("webbrowser.open") as mock_open, patch(
            "sys.stdout", new=io.StringIO()
        ) as mock_stdout:
            zulip_clickup.main()
            redirect_uri = "https://YourZulipApp.com"
            mock_open.assert_called_once_with(
                f"https://app.clickup.com/api?client_id={CLICKUP_CLIENT_ID}&redirect_uri={redirect_uri}"
            )
            expected_output = r"""
STEP 1
----
ClickUp authorization page will open in your browser\.
Please authorize your workspace\(s\)\.

Click 'Connect Workspace' on the page to proceed..."""

            self.assertRegex(
                mock_stdout.getvalue(),
                expected_output,
            )

    @mock_script_args()
    def test_query_for_auth_code(self) -> None:
        with patch("webbrowser.open"), patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            zulip_clickup.main()
            expected_output = r"""
STEP 2
----
After you've authorized your workspace,
you should be redirected to your home URL.
Please copy your home URL and paste it below.
It should contain a code, and look similar to this:

e.g. """ + re.escape(MOCK_AUTH_CODE_URL)
            self.assertRegex(
                mock_stdout.getvalue(),
                expected_output,
            )

    @mock_script_args()
    def test_select_clickup_events(self) -> None:
        with patch("webbrowser.open"), patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            zulip_clickup.main()
            expected_output = r"""
STEP 3
----
Please select which ClickUp event notification\(s\) you'd
like to receive in your Zulip app\.
EVENT CODES:
    1 = task
    2 = list
    3 = folder
    4 = space
    5 = goal

    Or, enter \* to subscribe to all events\.

Here's an example input if you intend to only receive notifications
related to task, list and folder: 1,2,3
"""
            self.assertRegex(
                mock_stdout.getvalue(),
                expected_output,
            )

    @mock_script_args()
    def test_success_message(self) -> None:
        with patch("webbrowser.open"), patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            zulip_clickup.main()
            expected_output = r"SUCCESS: Completed integrating your Zulip app with ClickUp!\s*webhook_id: \d+-\d+-\d+-\d+-\d+-\d+\s*You may delete this script or run it again to reconfigure\s*your integration\."
            self.assertRegex(mock_stdout.getvalue(), expected_output)

    @mock_script_args(selected_events="*")
    def test_select_all_events(self) -> None:
        with patch("webbrowser.open"), patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            zulip_clickup.main()
            expected_output = (
                r"Please enter a valid set of options and only select each option once"
            )
            self.assertNotRegex(
                mock_stdout.getvalue(),
                expected_output,
            )

    @mock_script_args(selected_events="123123")
    def test_select_invalid_events(self) -> None:
        with patch("webbrowser.open"), patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            with self.assertRaises(StopIteration):
                zulip_clickup.main()

            expected_output = (
                r"Please enter a valid set of options and only select each option once"
            )
            self.assertRegex(
                mock_stdout.getvalue(),
                expected_output,
            )

    @mock_script_args(selected_events="1,1,1,1")
    def test_invalid_input_multiple_events(self) -> None:
        with patch("webbrowser.open"), patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            with self.assertRaises(StopIteration):
                zulip_clickup.main()

            expected_output = (
                r"Please enter a valid set of options and only select each option once"
            )
            self.assertRegex(
                mock_stdout.getvalue(),
                expected_output,
            )

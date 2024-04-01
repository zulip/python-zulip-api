import io
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union
from unittest import TestCase
from unittest.mock import DEFAULT, patch

from integrations.clickup import zulip_clickup

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
    api_data_mapper: Dict[str, Dict[str, Dict[str, Any]]] = {  # path -> method -> response
        "oauth/token": {
            "POST": {"access_token": MOCK_API_KEY},
        },  # used for get_access_token()
        f"team/{CLICKUP_TEAM_ID}/webhook": {
            "POST": {"id": MOCK_CREATED_WEBHOOK_ID},
            "GET": {"webhooks": [MOCK_GET_WEBHOOK_IDS]},
        },  # used for create_webhook(), get_webhooks()
        f"webhook/{MOCK_DELETE_WEBHOOK_ID}": {"DELETE": {}},  # used for delete_webhook()
    }
    return api_data_mapper.get(path, {}).get(method, DEFAULT)


def mock_script_args() -> Callable[[Any], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            mock_user_inputs = [
                MOCK_WEBHOOK_URL,  # input for 1st step
                MOCK_AUTH_CODE_URL,  # input for 3rd step
                "1,2,3,4,5",  # third input for 4th step
            ]
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
            ), patch("os.system"), patch("time.sleep"), patch("sys.exit"), patch(
                "builtins.input", side_effect=mock_user_inputs
            ), patch(
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
                "clientid321", "clientsecret322", "teamid123", MOCK_WEBHOOK_URL
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
    def test_step_two(self) -> None:
        with patch("webbrowser.open") as mock_open, patch(
            "sys.stdout", new=io.StringIO()
        ) as mock_stdout:
            zulip_clickup.main()
            redirect_uri = "https://YourZulipApp.com"
            mock_open.assert_called_once_with(
                f"https://app.clickup.com/api?client_id=clientid321&redirect_uri={redirect_uri}"
            )
            expected_output = r"STEP 1[\s\S]*ClickUp authorization page will open in your browser\.[\s\S]*Please authorize your workspace\(s\)\.[\s\S]*Click 'Connect Workspace' on the page to proceed\.\.\."
            self.assertRegex(
                mock_stdout.getvalue(),
                expected_output,
            )

    @mock_script_args()
    def test_step_three(self) -> None:
        with patch("webbrowser.open"), patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            zulip_clickup.main()
            self.assertRegex(
                mock_stdout.getvalue(),
                (
                    r"STEP 2[\s\S]*After you've authorized your workspace,\s*you should be redirected to your home URL.\s*Please copy your home URL and paste it below.\s*It should contain a code, and look similar to this:\s*e.g. https://YourZulipDomain\.com/\?code=332KKA3321NNAK3MADS"
                ),
            )

    @mock_script_args()
    def test_step_four(self) -> None:
        with patch("webbrowser.open"), patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            zulip_clickup.main()
            self.assertRegex(
                mock_stdout.getvalue(),
                (
                    r"STEP 3[\s\S]*Please select which ClickUp event notification\(s\) you'd[\s\S]*like to receive in your Zulip app\.[\s\S]*EVENT CODES:[\s\S]*1 = task[\s\S]*2 = list[\s\S]*3 = folder[\s\S]*4 = space[\s\S]*5 = goals[\s\S]*Here's an example input if you intend to only receive notifications[\s\S]*related to task, list and folder: 1,2,3"
                ),
            )

    @mock_script_args()
    def test_final_step(self) -> None:
        with patch("webbrowser.open"), patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            zulip_clickup.main()
            self.assertRegex(
                mock_stdout.getvalue(),
                (
                    r"SUCCESS: Completed integrating your Zulip app with ClickUp!\s*webhook_id: \d+-\d+-\d+-\d+-\d+-\d+\s*You may delete this script or run it again to reconfigure\s*your integration\."
                ),
            )

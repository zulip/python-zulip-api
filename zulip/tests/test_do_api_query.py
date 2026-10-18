from unittest import TestCase
from unittest.mock import MagicMock, patch

import requests

import zulip


def make_client() -> zulip.Client:
    server_settings = {
        "zulip_version": "1.0",
        "zulip_feature_level": 0,
    }
    with patch.object(zulip.Client, "get_server_settings", return_value=server_settings):
        return zulip.Client(
            email="test@example.com",
            api_key="fake-key",
            site="https://example.com",
        )


class TestDoApiQuery(TestCase):
    def test_connection_error_resets_session(self) -> None:
        client = make_client()
        client.has_connected = True

        stale_session = MagicMock(spec=requests.Session)
        stale_session.request.side_effect = requests.exceptions.ConnectionError(
            "Connection reset by peer"
        )
        client.session = stale_session

        fresh_session = MagicMock(spec=requests.Session)
        fresh_session.headers = {}
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        response.json.return_value = {"result": "success", "msg": ""}
        fresh_session.request.return_value = response

        with (
            patch("zulip.requests.Session", return_value=fresh_session) as session_constructor,
            patch("zulip.time.sleep"),
        ):
            result = client.do_api_query({}, "api/v1/messages", method="GET")

        stale_session.close.assert_called_once_with()
        session_constructor.assert_called_once_with()
        fresh_session.request.assert_called_once()
        self.assertIs(client.session, fresh_session)
        self.assertEqual(result, {"result": "success", "msg": ""})

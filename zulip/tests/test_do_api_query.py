import unittest
from unittest.mock import MagicMock, patch

import requests

import zulip


def make_client() -> zulip.Client:
    with patch.object(zulip.Client, "call_endpoint") as mock_call:
        mock_call.return_value = {
            "result": "success",
            "zulip_version": "9.0.0",
            "zulip_feature_level": 300,
            "msg": "",
        }
        client = zulip.Client(
            email="test@example.com",
            api_key="deadbeef",
            site="https://testserver",
        )
    return client


class TestStaleConnectionRetry(unittest.TestCase):
    def test_stale_connection_resets_session(self) -> None:
        client = make_client()

        # Simulate a session that has already been used (has_connected = True)
        stale_session = MagicMock()
        client.session = stale_session
        client.has_connected = True

        # First request raises ConnectionError (stale socket),
        # second request succeeds
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"result": "success", "msg": ""}

        stale_session.request.side_effect = requests.exceptions.ConnectionError("stale")

        fresh_session = MagicMock()
        fresh_session.request.return_value = success_response

        call_count = 0

        def mock_ensure_session(self: zulip.Client) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: leave the stale session in place
                self.session = stale_session
            else:
                # Subsequent calls: provide a fresh session
                self.session = fresh_session

        with patch.object(zulip.Client, "ensure_session", mock_ensure_session):
            result = client.do_api_query({}, "/api/v1/messages", method="POST")

        # The stale session should have been closed
        stale_session.close.assert_called_once()

        # The result should come from the fresh session
        self.assertEqual(result, {"result": "success", "msg": ""})

        # ensure_session should have been called twice (once per loop iteration)
        self.assertEqual(call_count, 2)


if __name__ == "__main__":
    unittest.main()

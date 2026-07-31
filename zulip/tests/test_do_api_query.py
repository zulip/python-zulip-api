from unittest import TestCase
from unittest.mock import MagicMock, patch

import requests

import zulip


class TestDoApiQuery(TestCase):
    @patch("zulip.Client.get_server_settings")
    def _make_client(self, mock_server_settings: MagicMock) -> zulip.Client:
        mock_server_settings.return_value = {
            "zulip_version": "1.0",
            "zulip_feature_level": 0,
        }
        client = zulip.Client(
            email="test@example.com",
            api_key="fake-key",
            site="https://example.com",
        )
        client.has_connected = True
        return client

    def test_session_reset_on_connection_error(self) -> None:
        """When a ConnectionError occurs and the client has previously
        connected, the stale session should be closed and replaced with
        a fresh one so that the retry succeeds.
        """
        client = self._make_client()

        stale_session = MagicMock(spec=requests.Session)
        stale_session.request.side_effect = requests.exceptions.ConnectionError(
            "Connection reset by peer"
        )

        fresh_session = MagicMock(spec=requests.Session)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success", "msg": ""}
        fresh_session.request.return_value = mock_response

        # Track how many sessions ensure_session has built.
        sessions_created = 0

        def mock_ensure_session(self: zulip.Client) -> None:
            nonlocal sessions_created
            if self.session is None:
                sessions_created += 1
                if sessions_created == 1:
                    self.session = stale_session
                else:
                    self.session = fresh_session

        with patch.object(zulip.Client, "ensure_session", mock_ensure_session):
            result = client.do_api_query({}, "v1/messages", method="GET")

        # The stale session should have been closed.
        stale_session.close.assert_called_once()

        # A fresh session should have been created for the retry.
        self.assertEqual(sessions_created, 2)

        # The request should ultimately succeed.
        self.assertEqual(result["result"], "success")

    def test_session_not_reset_when_never_connected(self) -> None:
        """When the client has never successfully connected, a
        ConnectionError should raise UnrecoverableNetworkError
        without resetting the session.
        """
        client = self._make_client()
        client.has_connected = False

        mock_session = MagicMock(spec=requests.Session)
        mock_session.request.side_effect = requests.exceptions.ConnectionError("Connection refused")
        client.session = mock_session

        with self.assertRaises(zulip.UnrecoverableNetworkError):
            client.do_api_query({}, "v1/messages", method="GET")

        # The session should NOT have been closed, since we never
        # connected in the first place.
        mock_session.close.assert_not_called()

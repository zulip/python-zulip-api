from unittest import TestCase
from unittest.mock import MagicMock, patch

import requests
from typing_extensions import override

import zulip
from zulip import UnrecoverableNetworkError, ZulipError


class TestFetchUpload(TestCase):
    @override
    def setUp(self) -> None:
        # Avoid a real network request in Client.__init__, which calls
        # get_server_settings().
        patcher = patch.object(
            zulip.Client,
            "get_server_settings",
            return_value={"zulip_version": "10.0", "zulip_feature_level": 300},
        )
        self.addCleanup(patcher.stop)
        patcher.start()

        self.client = zulip.Client(
            email="bot@example.com",
            api_key="test-api-key",
            site="https://chat.zulip.org",
        )
        self.mock_session = MagicMock()
        self.client.session = self.mock_session

    def mock_response(self, status_code: int = 200, content: bytes = b"file-bytes") -> MagicMock:
        response = MagicMock()
        response.status_code = status_code
        response.content = content
        return response

    def test_fetch_upload_relative_path(self) -> None:
        self.mock_session.request.return_value = self.mock_response()
        content = self.client.fetch_upload("/user_uploads/1/abc123/file.png")
        self.assertEqual(content, b"file-bytes")
        self.mock_session.request.assert_called_once_with(
            "GET",
            "https://chat.zulip.org/user_uploads/1/abc123/file.png",
            timeout=15.0,
        )

    def test_fetch_upload_path_without_leading_slash(self) -> None:
        self.mock_session.request.return_value = self.mock_response()
        self.client.fetch_upload("user_uploads/1/abc123/file.png")
        self.mock_session.request.assert_called_once_with(
            "GET",
            "https://chat.zulip.org/user_uploads/1/abc123/file.png",
            timeout=15.0,
        )

    def test_fetch_upload_full_url(self) -> None:
        self.mock_session.request.return_value = self.mock_response()
        self.client.fetch_upload("https://chat.zulip.org/user_uploads/1/abc123/file.png")
        self.mock_session.request.assert_called_once_with(
            "GET",
            "https://chat.zulip.org/user_uploads/1/abc123/file.png",
            timeout=15.0,
        )

    def test_fetch_upload_temporary_url(self) -> None:
        self.mock_session.request.return_value = self.mock_response()
        self.client.fetch_upload("/user_uploads/temporary/abc123/file.png")
        self.mock_session.request.assert_called_once_with(
            "GET",
            "https://chat.zulip.org/user_uploads/temporary/abc123/file.png",
            timeout=15.0,
        )

    def test_fetch_upload_strips_api_v1_prefix_from_path(self) -> None:
        # GET /api/v1/user_uploads/... only returns a temporary access
        # URL as JSON, not the file itself, so the prefix must be
        # stripped to hit the direct download endpoint.
        self.mock_session.request.return_value = self.mock_response()
        self.client.fetch_upload("/api/v1/user_uploads/1/abc123/file.png")
        self.mock_session.request.assert_called_once_with(
            "GET",
            "https://chat.zulip.org/user_uploads/1/abc123/file.png",
            timeout=15.0,
        )

    def test_fetch_upload_strips_api_v1_prefix_from_full_url(self) -> None:
        self.mock_session.request.return_value = self.mock_response()
        self.client.fetch_upload(
            "https://chat.zulip.org/api/v1/user_uploads/1/abc123/file.png?token=xyz"
        )
        self.mock_session.request.assert_called_once_with(
            "GET",
            "https://chat.zulip.org/user_uploads/1/abc123/file.png?token=xyz",
            timeout=15.0,
        )

    def test_fetch_upload_custom_timeout(self) -> None:
        self.mock_session.request.return_value = self.mock_response()
        self.client.fetch_upload("/user_uploads/1/abc123/file.png", timeout=5.0)
        self.mock_session.request.assert_called_once_with(
            "GET",
            "https://chat.zulip.org/user_uploads/1/abc123/file.png",
            timeout=5.0,
        )

    def test_fetch_upload_rejects_absolute_url_on_other_host(self) -> None:
        # The bot's credentials must never be sent to an external host,
        # e.g. a link extracted from user message markdown.
        with self.assertRaises(ZulipError):
            self.client.fetch_upload("https://evil.example.com/user_uploads/1/abc/file.png")
        self.mock_session.request.assert_not_called()

    def test_fetch_upload_http_error(self) -> None:
        self.mock_session.request.return_value = self.mock_response(status_code=404)
        with self.assertRaises(ZulipError):
            self.client.fetch_upload("/user_uploads/1/abc123/file.png")

    def test_fetch_upload_connection_error(self) -> None:
        self.mock_session.request.side_effect = requests.exceptions.ConnectionError
        with self.assertRaises(UnrecoverableNetworkError):
            self.client.fetch_upload("/user_uploads/1/abc123/file.png")

from unittest.mock import MagicMock, patch

import pytest
import requests

from zulip import Client, UnrecoverableNetworkError, ZulipError


def make_client() -> Client:
    with patch.object(
        Client,
        "get_server_settings",
        return_value={"zulip_version": "test-version", "zulip_feature_level": 1},
    ):
        return Client(
            email="test@example.com",
            api_key="test-api-key",
            site="https://zulip.example.com",
            client="test-client",
        )


def mock_response(status_code: int, content: bytes) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.content = content
    return response


class TestFetchUpload:
    def test_absolute_url_passthrough(self) -> None:
        client = make_client()
        client.ensure_session()
        assert client.session is not None
        with patch.object(
            client.session, "get", return_value=mock_response(200, b"file contents")
        ) as mock_get:
            result = client.fetch_upload("https://zulip.example.com/user_uploads/1/file.pdf")
        mock_get.assert_called_once_with(
            "https://zulip.example.com/user_uploads/1/file.pdf", timeout=90.0
        )
        assert result == b"file contents"

    def test_absolute_url_api_v1_prefix_stripped(self) -> None:
        client = make_client()
        client.ensure_session()
        assert client.session is not None
        with patch.object(
            client.session, "get", return_value=mock_response(200, b"file contents")
        ) as mock_get:
            client.fetch_upload(
                "https://zulip.example.com/api/v1/user_uploads/1/file.pdf?token=xyz"
            )
        mock_get.assert_called_once_with(
            "https://zulip.example.com/user_uploads/1/file.pdf?token=xyz", timeout=90.0
        )

    def test_temporary_token_url(self) -> None:
        client = make_client()
        client.ensure_session()
        assert client.session is not None
        with patch.object(
            client.session, "get", return_value=mock_response(200, b"file contents")
        ) as mock_get:
            client.fetch_upload("/user_uploads/temporary/token123/file.pdf")
        mock_get.assert_called_once_with(
            "https://zulip.example.com/user_uploads/temporary/token123/file.pdf",
            timeout=90.0,
        )

    def test_absolute_url_on_other_origin_rejected(self) -> None:
        client = make_client()
        client.ensure_session()
        assert client.session is not None
        with patch.object(client.session, "get") as mock_get:
            with pytest.raises(ZulipError):
                client.fetch_upload("https://evil.example.com/user_uploads/1/file.pdf")
        mock_get.assert_not_called()

    def test_absolute_url_with_different_scheme_rejected(self) -> None:
        client = make_client()
        client.ensure_session()
        assert client.session is not None
        with patch.object(client.session, "get") as mock_get:
            with pytest.raises(ZulipError):
                client.fetch_upload("http://zulip.example.com/user_uploads/1/file.pdf")
        mock_get.assert_not_called()

    def test_root_relative_path_resolved_against_server_root(self) -> None:
        client = make_client()
        client.ensure_session()
        assert client.session is not None
        with patch.object(
            client.session, "get", return_value=mock_response(200, b"file contents")
        ) as mock_get:
            result = client.fetch_upload("/user_uploads/1/file.pdf")
        mock_get.assert_called_once_with(
            "https://zulip.example.com/user_uploads/1/file.pdf", timeout=90.0
        )
        assert result == b"file contents"

    def test_custom_timeout(self) -> None:
        client = make_client()
        client.ensure_session()
        assert client.session is not None
        with patch.object(
            client.session, "get", return_value=mock_response(200, b"file contents")
        ) as mock_get:
            client.fetch_upload("/user_uploads/1/file.pdf", timeout=5)
        mock_get.assert_called_once_with(
            "https://zulip.example.com/user_uploads/1/file.pdf", timeout=5.0
        )

    def test_path_without_leading_slash_accepted(self) -> None:
        client = make_client()
        client.ensure_session()
        assert client.session is not None
        with patch.object(
            client.session, "get", return_value=mock_response(200, b"file contents")
        ) as mock_get:
            client.fetch_upload("user_uploads/1/file.pdf")
        mock_get.assert_called_once_with(
            "https://zulip.example.com/user_uploads/1/file.pdf", timeout=90.0
        )

    def test_path_api_v1_prefix_stripped(self) -> None:
        client = make_client()
        client.ensure_session()
        assert client.session is not None
        with patch.object(
            client.session, "get", return_value=mock_response(200, b"file contents")
        ) as mock_get:
            client.fetch_upload("/api/v1/user_uploads/1/file.pdf")
        mock_get.assert_called_once_with(
            "https://zulip.example.com/user_uploads/1/file.pdf", timeout=90.0
        )

    def test_non_user_uploads_path_rejected(self) -> None:
        client = make_client()
        with pytest.raises(ZulipError):
            client.fetch_upload("random/path/here")

    def test_non_200_raises(self) -> None:
        client = make_client()
        client.ensure_session()
        assert client.session is not None
        with patch.object(
            client.session, "get", return_value=mock_response(403, b"")
        ), pytest.raises(ZulipError):
            client.fetch_upload("/user_uploads/1/file.pdf")

    def test_connection_error_raises_unrecoverable(self) -> None:
        client = make_client()
        client.ensure_session()
        assert client.session is not None
        with patch.object(
            client.session,
            "get",
            side_effect=requests.exceptions.ConnectionError("boom"),
        ):
            with pytest.raises(UnrecoverableNetworkError):
                client.fetch_upload("/user_uploads/1/file.pdf")

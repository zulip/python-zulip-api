"""Tests for Client.fetch_upload().

These tests verify that fetch_upload():
  1. Makes a GET request to the correct URL — WITHOUT the /api/v1/ prefix.
  2. Sends the request with the bot's HTTP Basic Auth credentials.
  3. Returns a raw requests.Response object (not JSON).
  4. Handles both relative paths and full URLs correctly.
"""

from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock, patch


def _make_client(site: str = "https://chat.example.com") -> Any:
    """Return a zulip.Client with its __init__ network calls mocked out."""
    import zulip

    # We patch both the network call inside __init__ (get_server_settings)
    # and ensure_session so we can inspect the session.session.get() call.
    with patch.object(
        zulip.Client,
        "get_server_settings",
        return_value={"zulip_version": "7.0.0", "zulip_feature_level": 100},
    ):
        client = zulip.Client(
            email="bot@example.com",
            api_key="deadbeef",
            site=site,
        )
    return client


class TestFetchUploadURLBuilding(TestCase):
    """Verify that the correct URL is constructed before making the request."""

    def _make_request(self, site: str, path: str) -> str:
        """Helper: return the URL that fetch_upload() would pass to session.get()."""
        client = _make_client(site=site)

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response

        client.session = mock_session

        client.fetch_upload(path)

        # Extract the URL that session.get() was called with.
        args, kwargs = mock_session.get.call_args
        return args[0]

    # ------------------------------------------------------------------
    # Relative path tests
    # ------------------------------------------------------------------

    def test_relative_path_builds_correct_url(self) -> None:
        url = self._make_request(
            site="https://chat.example.com",
            path="/user_uploads/2/ab/cat.png",
        )
        self.assertEqual(url, "https://chat.example.com/user_uploads/2/ab/cat.png")

    def test_relative_path_does_not_contain_api_v1(self) -> None:
        """The whole point of fetch_upload: /api/v1/ must NOT be prepended."""
        url = self._make_request(
            site="https://chat.example.com",
            path="/user_uploads/2/ab/cat.png",
        )
        self.assertNotIn("/api/v1/", url)

    def test_temporary_access_url(self) -> None:
        """Temporary access URLs (/user_uploads/temporary/...) also work."""
        url = self._make_request(
            site="https://chat.example.com",
            path="/user_uploads/temporary/tok3n/cat.png",
        )
        self.assertEqual(url, "https://chat.example.com/user_uploads/temporary/tok3n/cat.png")

    def test_path_without_leading_slash(self) -> None:
        """A path without a leading slash should still work."""
        url = self._make_request(
            site="https://chat.example.com",
            path="user_uploads/2/ab/cat.png",
        )
        self.assertEqual(url, "https://chat.example.com/user_uploads/2/ab/cat.png")

    # ------------------------------------------------------------------
    # Absolute URL tests (the caller already has a full URL)
    # ------------------------------------------------------------------

    def test_absolute_https_url_is_used_as_is(self) -> None:
        """If the caller passes a full https:// URL, it must not be modified."""
        full_url = "https://chat.example.com/user_uploads/2/ab/cat.png"
        url = self._make_request(
            site="https://chat.example.com",
            path=full_url,
        )
        self.assertEqual(url, full_url)

    def test_absolute_http_url_is_used_as_is(self) -> None:
        """Same check for http:// (useful in dev/test environments)."""
        full_url = "http://localhost:9991/user_uploads/1/ab/test.txt"
        url = self._make_request(
            site="http://localhost:9991",
            path=full_url,
        )
        self.assertEqual(url, full_url)

    # ------------------------------------------------------------------
    # Site URL normalisation
    # ------------------------------------------------------------------

    def test_site_with_custom_subdirectory(self) -> None:
        """Server hosted under a subpath is handled correctly."""
        url = self._make_request(
            site="https://example.com/zulip",
            path="/user_uploads/2/ab/cat.png",
        )
        # The base_url becomes 'https://example.com/zulip/api/', so the server
        # root should be 'https://example.com/zulip'.
        self.assertEqual(url, "https://example.com/zulip/user_uploads/2/ab/cat.png")


class TestFetchUploadAuthentication(TestCase):
    """Verify that the request is authenticated via the existing session."""

    def test_uses_authenticated_session(self) -> None:
        """fetch_upload() must use self.session (which carries auth headers),
        not a bare requests.get() call."""
        client = _make_client()

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response

        client.session = mock_session

        client.fetch_upload("/user_uploads/2/ab/cat.png")

        # Session.get must have been called exactly once.
        mock_session.get.assert_called_once()

    def test_ensure_session_is_called(self) -> None:
        """If there is no session yet, ensure_session() must be called."""
        client = _make_client()

        # Simulate a client with no session (as if network hadn't been used yet).
        client.session = None

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(client, "ensure_session") as mock_ensure_session:
            # After ensure_session is called, the session attribute needs to
            # exist; patch it in as a side effect.
            def _fake_ensure_session() -> None:
                mock_session = MagicMock()
                mock_session.get.return_value = mock_response
                client.session = mock_session

            mock_ensure_session.side_effect = _fake_ensure_session
            client.fetch_upload("/user_uploads/2/ab/cat.png")

        mock_ensure_session.assert_called_once()


class TestFetchUploadReturnValue(TestCase):
    """Verify that the raw requests.Response object is returned."""

    def test_returns_response_object(self) -> None:
        """fetch_upload must return the raw Response — not JSON."""
        import requests

        client = _make_client()

        fake_response = requests.Response()
        fake_response.status_code = 200
        fake_response._content = b"\x89PNG\r\n"  # noqa: SLF001  # first bytes of a PNG header

        mock_session = MagicMock()
        mock_session.get.return_value = fake_response
        client.session = mock_session

        result = client.fetch_upload("/user_uploads/2/ab/cat.png")

        self.assertIsInstance(result, requests.Response)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b"\x89PNG\r\n")

    def test_timeout_is_passed_to_session_get(self) -> None:
        """fetch_upload must set a timeout on the underlying HTTP call."""
        client = _make_client()

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        client.session = mock_session

        client.fetch_upload("/user_uploads/2/ab/cat.png")

        _, kwargs = mock_session.get.call_args
        self.assertIn("timeout", kwargs, "A timeout must be passed to session.get()")
        self.assertIsInstance(kwargs["timeout"], (int, float))

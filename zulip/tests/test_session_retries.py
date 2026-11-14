from unittest.mock import patch

from requests.adapters import HTTPAdapter

from zulip import Client


class TestSessionRetries:
    def test_session_has_retry_adapter(self) -> None:
        with patch.object(
            Client,
            "get_server_settings",
            return_value={"zulip_version": "test-version", "zulip_feature_level": 1},
        ):
            client = Client(
                email="test@example.com",
                api_key="test-api-key",
                site="https://zulip.example.com",
                client="test-client",
            )
            client.ensure_session()
            session = client.session
            assert session is not None
            for scheme in ("http://", "https://"):
                adapter = session.get_adapter(scheme)
                assert isinstance(adapter, HTTPAdapter)
                retries = adapter.max_retries
                assert retries.total == 3
                assert retries.connect == 3
                assert retries.read == 3
                assert retries.status == 0
                # POST and other methods must also be retried, because
                # requests over a stale pooled connection never reach
                # the server.
                assert retries.allowed_methods is None

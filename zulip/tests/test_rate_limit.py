import io
from typing import Any, Dict, Optional
from unittest import TestCase
from unittest.mock import MagicMock, patch

import zulip


def _make_response(
    status_code: int,
    json_data: Dict[str, Any],
    headers: Optional[Dict[str, Any]] = None,
) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {}
    response.json.return_value = json_data
    return response


class TestRateLimitRetry(TestCase):
    def _create_client(
        self,
        auto_retry_rate_limits: bool = False,
        verbose: bool = False,
    ) -> zulip.Client:
        with patch.object(
            zulip.Client,
            "get_server_settings",
            return_value={"zulip_version": "9.0", "zulip_feature_level": 270},
        ):
            return zulip.Client(
                email="test@example.com",
                api_key="test_api_key",
                site="https://chat.example.com",
                auto_retry_rate_limits=auto_retry_rate_limits,
                verbose=verbose,
            )

    @patch("time.sleep")
    def test_rate_limit_no_retry_by_default(self, mock_sleep: MagicMock) -> None:
        client = self._create_client()
        rate_limit_json = {
            "result": "error",
            "msg": "API usage exceeded rate limit",
            "code": "RATE_LIMIT_HIT",
            "retry-after": 2.5,
        }
        rate_limit_response = _make_response(429, rate_limit_json, headers={"Retry-After": "2.5"})

        client.ensure_session()
        assert client.session is not None
        with patch.object(
            client.session, "request", return_value=rate_limit_response
        ) as mock_request:
            result = client.do_api_query({}, "messages")

        self.assertEqual(result, rate_limit_json)
        self.assertEqual(mock_request.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_rate_limit_auto_retry_uses_retry_after_header(self, mock_sleep: MagicMock) -> None:
        client = self._create_client(auto_retry_rate_limits=True, verbose=True)
        rate_limit_response = _make_response(
            429,
            {
                "result": "error",
                "msg": "API usage exceeded rate limit",
                "code": "RATE_LIMIT_HIT",
                "retry-after": 2.5,
            },
            headers={"Retry-After": "2.5"},
        )
        success_json = {"result": "success", "msg": "", "id": 42}
        success_response = _make_response(200, success_json)

        client.ensure_session()
        assert client.session is not None
        with patch.object(
            client.session,
            "request",
            side_effect=[rate_limit_response, success_response],
        ) as mock_request:
            with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
                result = client.do_api_query({}, "messages")

        self.assertEqual(result, success_json)
        self.assertEqual(mock_request.call_count, 2)
        mock_sleep.assert_called_once_with(2.5)
        self.assertIn(
            "Rate limit hit! Sleeping for 2.5 seconds before retrying...",
            mock_stdout.getvalue(),
        )

    @patch("time.sleep")
    def test_rate_limit_auto_retry_fallback_wait_time(self, mock_sleep: MagicMock) -> None:
        client = self._create_client(auto_retry_rate_limits=True)
        missing_header_response = _make_response(
            429,
            {"result": "error", "code": "RATE_LIMIT_HIT"},
            headers={},
        )
        invalid_header_response = _make_response(
            429,
            {"result": "error", "code": "RATE_LIMIT_HIT"},
            headers={"Retry-After": "invalid"},
        )
        success_json = {"result": "success", "msg": ""}
        success_response = _make_response(200, success_json)

        client.ensure_session()
        assert client.session is not None
        with patch.object(
            client.session,
            "request",
            side_effect=[
                missing_header_response,
                invalid_header_response,
                success_response,
            ],
        ) as mock_request:
            result = client.do_api_query({}, "messages")

        self.assertEqual(result, success_json)
        self.assertEqual(mock_request.call_count, 3)
        self.assertEqual(mock_sleep.call_args_list, [((1.0,),), ((1.0,),)])

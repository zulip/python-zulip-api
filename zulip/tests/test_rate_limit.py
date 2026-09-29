import json
from typing import Any, Dict, Optional
from unittest import TestCase
from unittest.mock import Mock, patch

import zulip


def _make_client(**kwargs: Any) -> zulip.Client:
    with patch.object(
        zulip.Client,
        "get_server_settings",
        return_value={"zulip_version": "10.0.0", "zulip_feature_level": 0},
    ):
        return zulip.Client(
            email="bot@example.com",
            api_key="x" * 32,
            site="https://example.zulipchat.com",
            **kwargs,
        )


def _response(
    status_code: int,
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Mock:
    res = Mock()
    res.status_code = status_code
    res.headers = headers or {}
    if payload is None:
        res.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    else:
        res.json.return_value = payload
    return res


class TestParseRetryAfter(TestCase):
    def test_json_retry_after_preferred(self) -> None:
        res = _response(
            429,
            {
                "result": "error",
                "code": "RATE_LIMIT_HIT",
                "msg": "rate limited",
                "retry-after": 2.5,
            },
            {"Retry-After": "9"},
        )
        self.assertEqual(zulip._parse_retry_after_seconds(res), 2.5)  # noqa: SLF001

    def test_retry_after_header_fallback(self) -> None:
        res = _response(429, {"result": "error", "code": "RATE_LIMIT_HIT", "msg": "rate limited"})
        res.headers = {"Retry-After": "3.25"}
        self.assertEqual(zulip._parse_retry_after_seconds(res), 3.25)  # noqa: SLF001

    def test_invalid_values_default_to_one(self) -> None:
        res = _response(429, None, {"Retry-After": "soon"})
        self.assertEqual(zulip._parse_retry_after_seconds(res), 1.0)  # noqa: SLF001

    def test_negative_values_default_to_one(self) -> None:
        res = _response(429, {"retry-after": -4})
        self.assertEqual(zulip._parse_retry_after_seconds(res), 1.0)  # noqa: SLF001


class TestAutoRetryRateLimits(TestCase):
    def test_default_does_not_retry_429(self) -> None:
        client = _make_client()
        client.session = Mock()
        client.session.request.return_value = _response(
            429,
            {"result": "error", "code": "RATE_LIMIT_HIT", "msg": "API usage exceeded rate limit"},
        )
        with patch("time.sleep") as sleep:
            result = client.do_api_query({}, "v1/messages")
        sleep.assert_not_called()
        self.assertEqual(result["code"], "RATE_LIMIT_HIT")
        self.assertEqual(client.session.request.call_count, 1)

    def test_retries_after_retry_after_then_succeeds(self) -> None:
        client = _make_client(auto_retry_rate_limits=True)
        client.session = Mock()
        limited = _response(
            429,
            {
                "result": "error",
                "code": "RATE_LIMIT_HIT",
                "msg": "API usage exceeded rate limit",
                "retry-after": 1.5,
            },
        )
        ok = _response(200, {"result": "success", "id": 1})
        client.session.request.side_effect = [limited, ok]
        with patch("time.sleep") as sleep, patch("random.uniform", return_value=0.1):
            result = client.do_api_query({}, "v1/messages")
        sleep.assert_called_once_with(1.6)
        self.assertEqual(result["result"], "success")
        self.assertEqual(client.session.request.call_count, 2)

    def test_stops_after_ten_rate_limit_retries(self) -> None:
        client = _make_client(auto_retry_rate_limits=True)
        client.session = Mock()
        limited = _response(
            429,
            {
                "result": "error",
                "code": "RATE_LIMIT_HIT",
                "msg": "rate limited",
                "retry-after": 0.01,
            },
        )
        client.session.request.return_value = limited
        with patch("time.sleep"), patch("random.uniform", return_value=0.0):
            result = client.do_api_query({}, "v1/messages")
        # 10 retries after the first 429 => 11 requests, then the error is returned.
        self.assertEqual(client.session.request.call_count, 11)
        self.assertEqual(result["code"], "RATE_LIMIT_HIT")

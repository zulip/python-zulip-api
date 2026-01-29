#!/usr/bin/env python3

import unittest
import time
import responses
from unittest.mock import patch, MagicMock
from zulip import Client

class TestRateLimitHandling(unittest.TestCase):
    """Test the automatic handling of RATE_LIMIT_HIT errors."""

    def setUp(self):
        # Create a test client with a mocked get_server_settings method
        with patch.object(Client, 'get_server_settings', return_value={"zulip_version": "1.0", "zulip_feature_level": 1}):
            self.client = Client(
                email="test@example.com",
                api_key="test_api_key",
                site="https://example.com",
            )
            # Make sure we have a session
            self.client.ensure_session()

    @responses.activate
    def test_rate_limit_retry_with_header(self):
        """Test that the client retries after a rate limit error with Retry-After header."""
        
        # Add a mocked response for the first request that returns a rate limit error
        responses.add(
            responses.POST,
            "https://example.com/api/v1/test_endpoint",
            json={"result": "error", "code": "RATE_LIMIT_HIT", "msg": "Rate limit hit"},
            status=429,
            headers={"Retry-After": "1"}  # 1 second retry
        )
        
        # Add a mocked response for the second request (after retry) that succeeds
        responses.add(
            responses.POST,
            "https://example.com/api/v1/test_endpoint",
            json={"result": "success", "msg": ""},
            status=200
        )
        
        # Mock time.sleep to avoid actually waiting during the test
        with patch('time.sleep') as mock_sleep:
            result = self.client.call_endpoint(url="test_endpoint")
            
            # Verify that sleep was called with the correct retry value
            mock_sleep.assert_called_once_with(1)
            
            # Verify that we got the success response
            self.assertEqual(result["result"], "success")
            
            # Verify that both responses were requested
            self.assertEqual(len(responses.calls), 2)

    @responses.activate
    def test_rate_limit_retry_without_header(self):
        """Test that the client retries after a rate limit error without Retry-After header."""
        
        # Add a mocked response for the first request that returns a rate limit error
        responses.add(
            responses.POST,
            "https://example.com/api/v1/test_endpoint",
            json={"result": "error", "code": "RATE_LIMIT_HIT", "msg": "Rate limit hit"},
            status=429
            # No Retry-After header
        )
        
        # Add a mocked response for the second request (after retry) that succeeds
        responses.add(
            responses.POST,
            "https://example.com/api/v1/test_endpoint",
            json={"result": "success", "msg": ""},
            status=200
        )
        
        # Mock time.sleep to avoid actually waiting during the test
        with patch('time.sleep') as mock_sleep:
            result = self.client.call_endpoint(url="test_endpoint")
            
            # Verify that sleep was called (with any value)
            mock_sleep.assert_called_once()
            
            # Verify that we got the success response
            self.assertEqual(result["result"], "success")
            
            # Verify that both responses were requested
            self.assertEqual(len(responses.calls), 2)

if __name__ == "__main__":
    unittest.main()

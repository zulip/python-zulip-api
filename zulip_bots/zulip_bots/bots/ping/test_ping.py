import json
import requests
from typing import Any, Callable, Dict, List
from unittest.mock import patch

from zulip_bots.test_file_utils import read_bot_fixture_data
from zulip_bots.test_lib import BotTestCase

def create_side_effect(bot_name: str, fixture_mapping: Dict[str, str]) -> Callable[..., requests.Response]:

    def get_response(api_url: str, **kwargs: Any) -> requests.Response:
        fixture_name = fixture_mapping[api_url]
        http_data = read_bot_fixture_data(bot_name, fixture_name)
        try:
            http_response = http_data['response']
            http_headers = http_data['response-headers']
        except KeyError:
            print("ERROR: Failed to find 'response' or 'response-headers' fields in fixture")
            raise

        mock_result = requests.Response()
        mock_result._content = json.dumps(http_response).encode()  # type: ignore # This modifies a "hidden" attribute.
        mock_result.status_code = http_headers.get('status', 200)
        return mock_result

    return get_response

class TestPingBot(BotTestCase):
    bot_name = 'ping'

    def test_invalid_host(self) -> None:
        with self.mock_http_conversation('invalid_host'):
            self.verify_reply('^*&^&*', "The hostname `^*&^&*` is invalid.")

    def test_unknown_host(self) -> None:
        with patch('requests.get') as mock_get:
            mock_get.side_effect = create_side_effect(self.bot_name, {
                'https://check-host.net/check-ping': 'unknown_host_1',
                'https://check-host.net/check-result/7113153kd9d': 'unknown_host_2'
            })
            responses = self.get_responses({'content': 'qwerty', 'type': 'stream'})

            self.assertEqual(responses[0]['content'],
                             "Checking availability of `qwerty`, please wait...")

            self.assertTrue(":cross_mark: Latvia, Riga (178.159.42.229) – Unknown host" in
                            responses[1]['content'])

    def test_correct_host(self) -> None:
        with patch('requests.get') as mock_get:
            mock_get.side_effect = create_side_effect(self.bot_name, {
                'https://check-host.net/check-ping': 'correct_host_1',
                'https://check-host.net/check-result/71135d1kc3a': 'correct_host_2'
            })
            responses = self.get_responses({'content': 'baidu.cn', 'type': 'stream'})

            self.assertEqual(responses[0]['content'],
                             "Checking availability of `baidu.cn`, please wait...")

            self.assertTrue(":cross_mark: Germany, Falkenstein (46.4.143.48) – Timed out" in
                            responses[1]['content'])

            self.assertTrue(":heavy_check_mark: Sweden, Stockholm (185.29.8.135)" in
                            responses[1]['content'])

            # The node is still performing the check.
            self.assertTrue("USA, North Carolina" not in responses[1]['content'])

from zulip_bots.test_lib import BotTestCase, DefaultTests, read_bot_fixture_data

from contextlib import contextmanager

from unittest.mock import patch

from typing import Iterator, ByteString

import json

class MockHttplibRequest():
    def __init__(self, response: str) -> None:
        self.response = response

    def read(self) -> ByteString:
        return json.dumps(self.response).encode()

class MockTextRequest():
    def __init__(self) -> None:
        self.session_id = ""
        self.query = ""
        self.response = ""

    def getresponse(self) -> MockHttplibRequest:
        return MockHttplibRequest(self.response)

@contextmanager
def mock_dialogflow(test_name: str, bot_name: str) -> Iterator[None]:
    response_data = read_bot_fixture_data(bot_name, test_name)
    try:
        df_request = response_data['request']
        df_response = response_data['response']
    except KeyError:
        print("ERROR: 'request' or 'response' field not found in fixture.")
        raise

    with patch('apiai.ApiAI.text_request') as mock_text_request:
        request = MockTextRequest()
        request.response = df_response
        mock_text_request.return_value = request
        yield

class TestDialogFlowBot(BotTestCase, DefaultTests):
    bot_name = 'dialogflow'

    def _test(self, test_name: str, message: str, response: str) -> None:
        with self.mock_config_info({'key': 'abcdefg', 'bot_info': 'bot info foo bar'}), \
                mock_dialogflow(test_name, 'dialogflow'):
            self.verify_reply(message, response)

    def test_normal(self) -> None:
        self._test('test_normal', 'hello', 'how are you?')

    def test_403(self) -> None:
        self._test('test_403', 'hello', 'Error 403: Access Denied.')

    def test_empty_response(self) -> None:
        self._test('test_empty_response', 'hello', 'Error. No result.')

    def test_exception(self) -> None:
        with patch('logging.exception'):
            self._test('test_exception', 'hello', 'Error. \'status\'.')

    def test_help(self) -> None:
        self._test('test_normal', 'help', 'bot info foo bar')
        self._test('test_normal', '', 'bot info foo bar')

    def test_alternate_response(self) -> None:
        self._test('test_alternate_result', 'hello', 'alternate result')

    def test_bot_responds_to_empty_message(self) -> None:
        with self.mock_config_info({'key': 'abcdefg', 'bot_info': 'bot info foo bar'}):
            pass

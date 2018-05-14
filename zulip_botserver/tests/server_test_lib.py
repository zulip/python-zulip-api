import json

from typing import Any, List, Dict, Optional
from unittest import TestCase
from zulip_botserver import server

class BotServerTestCase(TestCase):

    def setUp(self):
        # type: () -> None
        server.app.testing = True
        self.app = server.app.test_client()

    def assert_bot_server_response(self,
                                   available_bots=None,
                                   bots_config=None,
                                   bots_lib_module=None,
                                   bot_handlers=None,
                                   payload_url="/bots/helloworld",
                                   message=dict(message={'key': "test message"}),
                                   check_success=False,
                                   ):
        # type: (Optional[List[str]], Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]], str, Dict[str, Dict[str, Any]], bool) -> None
        if available_bots is not None:
            server.available_bots = available_bots
            server.bots_config = bots_config  # type: ignore # monkey-patching
            server.load_lib_modules()
            server.load_bot_handlers()

        response = self.app.post(payload_url, data=json.dumps(message))

        if check_success:
            assert 200 <= response.status_code < 300
        else:
            assert 400 <= response.status_code < 500

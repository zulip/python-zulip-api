from unittest import TestCase
import zulip_botserver.server
import json
from typing import Any, List, Dict, Mapping, Optional

class BotServerTestCase(TestCase):

    def setUp(self):
        # type: () -> None
        zulip_botserver.server.app.testing = True
        self.app = zulip_botserver.server.app.test_client()

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
            zulip_botserver.server.available_bots = available_bots
            zulip_botserver.server.bots_config = bots_config  # type: ignore # monkey-patching
            zulip_botserver.server.load_lib_modules()
            zulip_botserver.server.load_bot_handlers()

        response = self.app.post(payload_url, data=json.dumps(message))

        if check_success:
            assert response.status_code >= 200 and response.status_code < 300
        else:
            assert response.status_code >= 400 and response.status_code < 500

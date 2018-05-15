import json

from typing import Any, List, Dict, Optional, Union
from unittest import TestCase
from werkzeug.exceptions import BadRequest
from zulip_botserver import server


class BotServerTestCase(TestCase):

    def setUp(self) -> None:
        server.app.testing = True
        self.app = server.app.test_client()

    def assert_bot_server_response(self,
                                   available_bots: Optional[List[str]]=None,
                                   bots_config: Optional[Dict[str, Dict[str, str]]]=None,
                                   bots_lib_module: Optional[Dict[str, Any]]=None,
                                   bot_handlers: Optional[Union[Dict[str, Any], BadRequest]]=None,
                                   payload_url: str="/bots/helloworld",
                                   message: Optional[Dict[str, Any]]=dict(message={'key': "test message"}),
                                   check_success: bool=False,
                                   ) -> None:
        if available_bots is not None and bots_config is not None:
            server.available_bots = available_bots
            bots_lib_modules = server.load_lib_modules()
            server.app.config["BOTS_LIB_MODULES"] = bots_lib_modules
            if bot_handlers is None:
                bot_handlers = server.load_bot_handlers(bots_config, bots_lib_modules)
            if not isinstance(bot_handlers, BadRequest):
                server.app.config["BOT_HANDLERS"] = bot_handlers

        response = self.app.post(payload_url, data=json.dumps(message))

        if check_success:
            assert 200 <= response.status_code < 300
        else:
            assert 400 <= response.status_code < 500

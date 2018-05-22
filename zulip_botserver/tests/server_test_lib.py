import configparser
import json

from typing import Any, List, Dict, Optional
from unittest import TestCase
from zulip_botserver import server


class BotServerTestCase(TestCase):

    def setUp(self) -> None:
        server.app.testing = True
        self.app = server.app.test_client()

    def assert_bot_server_response(
        self,
        available_bots: Optional[List[str]]=None,
        bots_config: Optional[Dict[str, Dict[str, str]]]=None,
        bot_handlers: Optional[Dict[str, Any]]=None,
        message: Optional[Dict[str, Any]]=dict(message={'key': "test message"}),
        check_success: bool=False,
        third_party_bot_conf: Optional[configparser.ConfigParser]=None,
    ) -> None:
        if available_bots is not None and bots_config is not None:
            server.bots_config = bots_config
            bots_lib_modules = server.load_lib_modules(available_bots)
            server.app.config["BOTS_LIB_MODULES"] = bots_lib_modules
            if bot_handlers is None:
                bot_handlers = server.load_bot_handlers(available_bots, bots_config, third_party_bot_conf)
            message_handlers = server.init_message_handlers(available_bots, bots_lib_modules, bot_handlers)
            server.app.config["BOT_HANDLERS"] = bot_handlers
            server.app.config["MESSAGE_HANDLERS"] = message_handlers

        response = self.app.post(data=json.dumps(message))

        if check_success:
            assert 200 <= response.status_code < 300
        else:
            assert 400 <= response.status_code < 500

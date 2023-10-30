import configparser
import json
from typing import Any, Dict, List, Optional
from unittest import TestCase, mock

from typing_extensions import override

from zulip_botserver import server


class BotServerTestCase(TestCase):
    @override
    def setUp(self) -> None:
        server.app.testing = True
        self.app = server.app.test_client()

    @mock.patch("zulip_bots.lib.ExternalBotHandler")
    def assert_bot_server_response(
        self,
        mock_external_bot_handler: mock.Mock,
        available_bots: Optional[List[str]] = None,
        bots_config: Optional[Dict[str, Dict[str, str]]] = None,
        bot_handlers: Optional[Dict[str, Any]] = None,
        event: Optional[Dict[str, Any]] = None,
        expected_response: Optional[str] = None,
        check_success: bool = False,
        third_party_bot_conf: Optional[configparser.ConfigParser] = None,
    ) -> None:
        if available_bots is not None and bots_config is not None:
            server.bots_config = bots_config
            bots_lib_modules = server.load_lib_modules(available_bots)
            server.app.config["BOTS_LIB_MODULES"] = bots_lib_modules
            if bot_handlers is None:
                bot_handlers = server.load_bot_handlers(
                    available_bots, bots_lib_modules, bots_config, third_party_bot_conf
                )
            message_handlers = server.init_message_handlers(
                available_bots, bots_lib_modules, bot_handlers
            )
            server.app.config["BOT_HANDLERS"] = bot_handlers
            server.app.config["MESSAGE_HANDLERS"] = message_handlers

        mock_external_bot_handler.return_value.full_name = "test"
        response = self.app.post(data=json.dumps(event))

        # NOTE: Currently, assert_bot_server_response can only check the expected_response
        # for bots that use send_reply. However, the vast majority of bots use send_reply.
        # Therefore, the Botserver can be still be effectively tested.
        bot_send_reply_call = mock_external_bot_handler.return_value.send_reply
        if expected_response is not None:
            self.assertTrue(bot_send_reply_call.called)
            self.assertEqual(expected_response, bot_send_reply_call.call_args[0][1])
        else:
            self.assertFalse(bot_send_reply_call.called)

        if check_success:
            assert 200 <= response.status_code < 300
        else:
            assert 400 <= response.status_code < 500

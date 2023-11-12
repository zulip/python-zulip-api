import json
import os
from collections import OrderedDict
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any, Dict
from unittest import mock

import importlib_metadata as metadata
from typing_extensions import override

from zulip_bots.lib import BotHandler
from zulip_botserver import server
from zulip_botserver.input_parameters import parse_args

from .server_test_lib import BotServerTestCase


class BotServerTests(BotServerTestCase):
    class MockMessageHandler:
        def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
            assert message == {"key": "test message"}

    class MockLibModule:
        def handler_class(self) -> Any:
            return BotServerTests.MockMessageHandler()

    @override
    def setUp(self) -> None:
        # Since initializing Client invokes `get_server_settings` that fails in the test
        # environment, we need to mock it to pretend that there exists a backend.
        super().setUp()
        self.patch = mock.patch("zulip.Client.get_server_settings", return_value=mock.Mock())
        self.patch.start()

    def test_successful_request(self) -> None:
        available_bots = ["helloworld"]
        bots_config = {
            "helloworld": {
                "email": "helloworld-bot@zulip.com",
                "key": "123456789qwertyuiop",
                "site": "http://localhost",
                "token": "abcd1234",
            }
        }
        self.assert_bot_server_response(
            available_bots=available_bots,
            bots_config=bots_config,
            event=dict(
                message={"content": "@**test** test message"},
                bot_email="helloworld-bot@zulip.com",
                trigger="mention",
                token="abcd1234",  # noqa: S106
            ),
            expected_response="beep boop",
            check_success=True,
        )

    def test_successful_request_from_two_bots(self) -> None:
        available_bots = ["helloworld", "help"]
        bots_config = {
            "helloworld": {
                "email": "helloworld-bot@zulip.com",
                "key": "123456789qwertyuiop",
                "site": "http://localhost",
                "token": "abcd1234",
            },
            "help": {
                "email": "help-bot@zulip.com",
                "key": "123456789qwertyuiop",
                "site": "http://localhost",
                "token": "abcd1234",
            },
        }
        self.assert_bot_server_response(
            available_bots=available_bots,
            event=dict(
                message={"content": "@**test** test message"},
                bot_email="helloworld-bot@zulip.com",
                trigger="mention",
                token="abcd1234",  # noqa: S106
            ),
            expected_response="beep boop",
            bots_config=bots_config,
            check_success=True,
        )

    def test_request_for_unkown_bot(self) -> None:
        bots_config = {
            "helloworld": {
                "email": "helloworld-bot@zulip.com",
                "key": "123456789qwertyuiop",
                "site": "http://localhost",
                "token": "abcd1234",
            },
        }
        self.assert_bot_server_response(
            available_bots=["helloworld"],
            event=dict(message={"content": "test message"}, bot_email="unknown-bot@zulip.com"),
            bots_config=bots_config,
            check_success=False,
        )

    def test_wrong_bot_token(self) -> None:
        available_bots = ["helloworld"]
        bots_config = {
            "helloworld": {
                "email": "helloworld-bot@zulip.com",
                "key": "123456789qwertyuiop",
                "site": "http://localhost",
                "token": "abcd1234",
            }
        }
        self.assert_bot_server_response(
            available_bots=available_bots,
            bots_config=bots_config,
            event=dict(
                message={"content": "@**test** test message"},
                bot_email="helloworld-bot@zulip.com",
                trigger="mention",
                token="wrongtoken",  # noqa: S106
            ),
            check_success=False,
        )

    @mock.patch("logging.error")
    @mock.patch("zulip_bots.lib.StateHandler")
    def test_wrong_bot_credentials(
        self, mock_state_handler: mock.Mock, mock_logging_error: mock.Mock
    ) -> None:
        available_bots = ["nonexistent-bot"]
        bots_config = {
            "nonexistent-bot": {
                "email": "helloworld-bot@zulip.com",
                "key": "123456789qwertyuiop",
                "site": "http://localhost",
                "token": "abcd1234",
            }
        }
        with self.assertRaisesRegex(
            SystemExit,
            'Error: Bot "nonexistent-bot" doesn\'t exist. Please make '
            "sure you have set up the botserverrc file correctly.",
        ):
            self.assert_bot_server_response(
                available_bots=available_bots,
                event=dict(
                    message={"content": "@**test** test message"},
                    bot_email="helloworld-bot@zulip.com",
                    trigger="mention",
                    token="abcd1234",  # noqa: S106
                ),
                bots_config=bots_config,
            )

    @mock.patch("sys.argv", ["zulip-botserver", "--config-file", "/foo/bar/baz.conf"])
    def test_argument_parsing_defaults(self) -> None:
        opts = parse_args()
        assert opts.config_file == "/foo/bar/baz.conf"
        assert opts.bot_name is None
        assert opts.bot_config_file is None
        assert opts.hostname == "127.0.0.1"
        assert opts.port == 5002

    def test_read_config_from_env_vars(self) -> None:
        # We use an OrderedDict so that the order of the entries in
        # the stringified environment variable is standard even on
        # Python 3.7 and earlier.
        bots_config = OrderedDict()
        bots_config["hello_world"] = {
            "email": "helloworld-bot@zulip.com",
            "key": "value",
            "site": "http://localhost",
            "token": "abcd1234",
        }
        bots_config["giphy"] = {
            "email": "giphy-bot@zulip.com",
            "key": "value2",
            "site": "http://localhost",
            "token": "abcd1234",
        }
        os.environ["ZULIP_BOTSERVER_CONFIG"] = json.dumps(bots_config)

        # No bot specified; should read all bot configs
        assert server.read_config_from_env_vars() == bots_config

        # Specified bot exists; should read only that section.
        assert server.read_config_from_env_vars("giphy") == {"giphy": bots_config["giphy"]}

        # Specified bot doesn't exist; should read the first section of the config.
        assert server.read_config_from_env_vars("redefined_bot") == {
            "redefined_bot": bots_config["hello_world"]
        }

    def test_read_config_file(self) -> None:
        with self.assertRaises(IOError):
            server.read_config_file("nonexistentfile.conf")
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # No bot specified; should read all bot configs.
        bot_conf1 = server.read_config_file(os.path.join(current_dir, "test.conf"))
        expected_config1 = {
            "helloworld": {
                "email": "helloworld-bot@zulip.com",
                "key": "value",
                "site": "http://localhost",
                "token": "abcd1234",
            },
            "giphy": {
                "email": "giphy-bot@zulip.com",
                "key": "value2",
                "site": "http://localhost",
                "token": "abcd1234",
            },
        }
        assert json.dumps(bot_conf1, sort_keys=True) == json.dumps(expected_config1, sort_keys=True)

        # Specified bot exists; should read only that section.
        bot_conf3 = server.read_config_file(os.path.join(current_dir, "test.conf"), "giphy")
        expected_config3 = {
            "giphy": {
                "email": "giphy-bot@zulip.com",
                "key": "value2",
                "site": "http://localhost",
                "token": "abcd1234",
            }
        }
        assert json.dumps(bot_conf3, sort_keys=True) == json.dumps(expected_config3, sort_keys=True)

        # Specified bot doesn't exist; should read the first section of the config.
        bot_conf2 = server.read_config_file(os.path.join(current_dir, "test.conf"), "redefined_bot")
        expected_config2 = {
            "redefined_bot": {
                "email": "helloworld-bot@zulip.com",
                "key": "value",
                "site": "http://localhost",
                "token": "abcd1234",
            }
        }
        assert json.dumps(bot_conf2, sort_keys=True) == json.dumps(expected_config2, sort_keys=True)

    def test_load_lib_modules(self) -> None:
        # This testcase requires hardcoded paths, which here is a good thing so if we ever
        # restructure zulip_bots, this test would fail and we would also update Botserver
        # at the same time.
        helloworld = import_module("zulip_bots.bots.{bot}.{bot}".format(bot="helloworld"))
        root_dir = Path(__file__).parents[2].as_posix()
        # load valid module name
        module = server.load_lib_modules(["helloworld"])["helloworld"]
        assert module == helloworld

        # load valid file path
        path = Path(
            root_dir, "zulip_bots/zulip_bots/bots/{bot}/{bot}.py".format(bot="helloworld")
        ).as_posix()
        module = server.load_lib_modules([path])[path]
        assert module.__name__ == "custom_bot_module"
        assert module.__file__ == path
        assert isinstance(module, ModuleType)

        # load invalid module name
        with self.assertRaisesRegex(
            SystemExit,
            'Error: Bot "botserver-test-case-random-bot" doesn\'t exist. '
            "Please make sure you have set up the botserverrc file correctly.",
        ):
            module = server.load_lib_modules(["botserver-test-case-random-bot"])[
                "botserver-test-case-random-bot"
            ]

        # load invalid file path
        with self.assertRaisesRegex(
            SystemExit,
            f'Error: Bot "{root_dir}/zulip_bots/zulip_bots/bots/helloworld.py" doesn\'t exist. '
            "Please make sure you have set up the botserverrc file correctly.",
        ):
            path = Path(
                root_dir, "zulip_bots/zulip_bots/bots/{bot}.py".format(bot="helloworld")
            ).as_posix()
            module = server.load_lib_modules([path])[path]

    @mock.patch("zulip_botserver.server.app")
    @mock.patch("sys.argv", ["zulip-botserver", "--config-file", "/foo/bar/baz.conf"])
    def test_load_from_registry(self, mock_app: mock.Mock) -> None:
        packaged_bot_module = mock.MagicMock(__version__="1.0.0", __file__="asd")
        packaged_bot_entrypoint = metadata.EntryPoint(
            "packaged_bot", "module_name", "zulip_bots.registry"
        )
        bots_config = {
            "packaged_bot": {
                "email": "packaged-bot@zulip.com",
                "key": "value",
                "site": "http://localhost",
                "token": "abcd1234",
            }
        }

        with mock.patch(
            "zulip_botserver.server.read_config_file", return_value=bots_config
        ), mock.patch("zulip_botserver.server.lib.ExternalBotHandler", new=mock.Mock()), mock.patch(
            "zulip_bots.finder.metadata.EntryPoint.load",
            return_value=packaged_bot_module,
        ), mock.patch(
            "zulip_bots.finder.metadata.entry_points",
            return_value=(packaged_bot_entrypoint,),
        ):
            server.main()

        mock_app.config.__setitem__.assert_any_call(
            "BOTS_LIB_MODULES", {"packaged_bot": packaged_bot_module}
        )

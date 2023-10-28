import json
import os
from importlib import import_module
from typing import Any, Dict

"""
This module helps us find files in the bots directory.  Our
directory structure is currently:

    zulip_bots/zulip_bots/bots/
        <bot name>/
            <bot name>.py
            fixtures/
"""


def get_bot_message_handler(bot_name: str) -> Any:
    # message_handler is of type 'Any', since it can contain any bot's
    # handler class. Eventually, we want bot's handler classes to
    # inherit from a common prototype specifying the handle_message
    # function.
    lib_module: Any = import_module(f"zulip_bots.bots.{bot_name}.{bot_name}")
    return lib_module.handler_class()


def read_bot_fixture_data(bot_name: str, test_name: str) -> Dict[str, Any]:
    base_path = os.path.realpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "bots", bot_name, "fixtures")
    )
    http_data_path = os.path.join(base_path, f"{test_name}.json")
    with open(http_data_path, encoding="utf-8") as f:
        content = f.read()
    http_data = json.loads(content)
    return http_data

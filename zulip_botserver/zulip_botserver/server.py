import configparser
import json
import os
import sys

from flask import Flask, request
from importlib import import_module
from typing import Any, Dict, Union, List
from werkzeug.exceptions import BadRequest

from zulip import Client
from zulip_bots.custom_exceptions import ConfigValidationError
from zulip_bots.lib import ExternalBotHandler, StateHandler

available_bots = []  # type: List[str]


def read_config_file(config_file_path: str) -> Dict[str, Dict[str, str]]:
    config_file_path = os.path.abspath(os.path.expanduser(config_file_path))
    if not os.path.isfile(config_file_path):
        raise IOError("Could not read config file {}: File not found.".format(config_file_path))
    parser = configparser.ConfigParser()
    parser.read(config_file_path)

    bots_config = {}
    for section in parser.sections():
        bots_config[section] = {
            "email": parser.get(section, 'email'),
            "key": parser.get(section, 'key'),
            "site": parser.get(section, 'site'),
        }
    return bots_config


def load_lib_modules() -> Dict[str, Any]:
    bots_lib_module = {}
    for bot in available_bots:
        try:
            module_name = 'zulip_bots.bots.{bot}.{bot}'.format(bot=bot)
            lib_module = import_module(module_name)
            bots_lib_module[bot] = lib_module
        except ImportError:
            raise ImportError(
                "\nImport Error: Bot \"{}\" doesn't exists. "
                "Please make sure you have set up the flaskbotrc file correctly.\n".format(bot)
            )
    return bots_lib_module


def load_bot_handlers(
    bots_config: Dict[str, Dict[str, str]],
    bots_lib_module: Dict[str, Any],
) -> Union[Dict[str, ExternalBotHandler], BadRequest]:
    bot_handlers = {}
    for bot in available_bots:
        client = Client(email=bots_config[bot]["email"],
                        api_key=bots_config[bot]["key"],
                        site=bots_config[bot]["site"])
        try:
            bot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'bots', bot)
            # TODO: Figure out how to pass in third party config info.
            bot_handler = ExternalBotHandler(
                client,
                bot_dir,
                bot_details={},
                bot_config_file=None
            )
            bot_handlers[bot] = bot_handler

            lib_module = bots_lib_module[bot]
            message_handler = lib_module.handler_class()
            if hasattr(message_handler, 'validate_config'):
                config_data = bot_handlers[bot].get_config_info(bot)
                try:
                    lib_module.handler_class.validate_config(config_data)
                except ConfigValidationError as e:
                    print("There was a problem validating your config file:\n\n{}".format(e))
                    sys.exit(1)

            if hasattr(message_handler, 'initialize'):
                message_handler.initialize(bot_handler=bot_handler)
        except SystemExit:
            return BadRequest("Cannot fetch user profile for bot {}, make sure you have set up the flaskbotrc "
                              "file correctly.".format(bot))
    return bot_handlers


app = Flask(__name__)


@app.route('/bots/<bot>', methods=['POST'])
def handle_bot(bot: str) -> Union[str, BadRequest]:
    lib_module = app.config.get("BOTS_LIB_MODULES", {}).get(bot)
    if lib_module is None:
        return BadRequest("Can't find the configuration or Bot Handler code for bot {}. "
                          "Make sure that the `zulip_bots` package is installed, and "
                          "that your flaskbotrc is set up correctly".format(bot))
    message_handler = lib_module.handler_class()

    event = request.get_json(force=True)
    message_handler.handle_message(message=event["message"],
                                   bot_handler=app.config["BOT_HANDLERS"].get(bot))
    return json.dumps("")


def main() -> None:
    options = parse_args()
    bots_config = read_config_file(options.config_file)
    global available_bots
    available_bots = list(bots_config.keys())
    bots_lib_modules = load_lib_modules()
    bot_handlers = load_bot_handlers(bots_config, bots_lib_modules)
    app.config["BOTS_LIB_MODULES"] = bots_lib_modules
    app.config["BOT_HANDLERS"] = bot_handlers
    app.run(host=options.hostname, port=int(options.port), debug=True)

if __name__ == '__main__':
    main()

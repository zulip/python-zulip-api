import configparser
import logging
import json
import os

from flask import Flask, request
from importlib import import_module
from typing import Any, Dict, Union, List, Optional
from werkzeug.exceptions import BadRequest

from zulip import Client
from zulip_bots import lib
from zulip_botserver.input_parameters import parse_args


def read_config_file(config_file_path: str, bot_name: Optional[str]=None) -> Dict[str, Dict[str, str]]:
    parser = parse_config_file(config_file_path)

    bots_config = {}  # type: Dict[str, Dict[str, str]]
    for section in parser.sections():
        section_info = {
            "email": parser.get(section, 'email'),
            "key": parser.get(section, 'key'),
            "site": parser.get(section, 'site'),
        }
        if bot_name is not None:
            logging.warning("Single bot mode is enabled")
            if bots_config:
                logging.warning("'{}' bot will be ignored".format(section))
            else:
                bots_config[bot_name] = section_info
                logging.warning(
                    "First bot name in the config list was changed from '{}' to '{}'".format(section, bot_name)
                )
        else:
            bots_config[section] = section_info
    return bots_config


def parse_config_file(config_file_path: str) -> configparser.ConfigParser:
    config_file_path = os.path.abspath(os.path.expanduser(config_file_path))
    if not os.path.isfile(config_file_path):
        raise IOError("Could not read config file {}: File not found.".format(config_file_path))
    parser = configparser.ConfigParser()
    parser.read(config_file_path)
    return parser


def load_lib_modules(available_bots: List[str]) -> Dict[str, Any]:
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
    available_bots: List[str],
    bots_config: Dict[str, Dict[str, str]],
    third_party_bot_conf: Optional[configparser.ConfigParser]=None,
) -> Dict[str, lib.ExternalBotHandler]:
    bot_handlers = {}
    for bot in available_bots:
        client = Client(email=bots_config[bot]["email"],
                        api_key=bots_config[bot]["key"],
                        site=bots_config[bot]["site"])
        bot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bots', bot)
        bot_handler = lib.ExternalBotHandler(
            client,
            bot_dir,
            bot_details={},
            bot_config_parser=third_party_bot_conf
        )

        bot_handlers[bot] = bot_handler
    return bot_handlers


def init_message_handlers(
    available_bots: List[str],
    bots_lib_modules: Dict[str, Any],
    bot_handlers: Dict[str, lib.ExternalBotHandler],
) -> Dict[str, Any]:
    message_handlers = {}
    for bot in available_bots:
        bot_lib_module = bots_lib_modules[bot]
        bot_handler = bot_handlers[bot]
        message_handler = lib.prepare_message_handler(bot, bot_handler, bot_lib_module)
        message_handlers[bot] = message_handler
    return message_handlers


app = Flask(__name__)


@app.route('/bots/<bot>', methods=['POST'])
def handle_bot(bot: str) -> Union[str, BadRequest]:
    lib_module = app.config.get("BOTS_LIB_MODULES", {}).get(bot)
    bot_handler = app.config.get("BOT_HANDLERS", {}).get(bot)
    message_handler = app.config.get("MESSAGE_HANDLERS", {}).get(bot)
    if lib_module is None:
        return BadRequest("Can't find the configuration or Bot Handler code for bot {}. "
                          "Make sure that the `zulip_bots` package is installed, and "
                          "that your flaskbotrc is set up correctly".format(bot))

    event = request.get_json(force=True)
    message_handler.handle_message(message=event["message"], bot_handler=bot_handler)
    return json.dumps("")


def main() -> None:
    options = parse_args()
    bots_config = read_config_file(options.config_file, options.bot_name)
    available_bots = list(bots_config.keys())
    bots_lib_modules = load_lib_modules(available_bots)
    third_party_bot_conf = parse_config_file(options.bot_config_file) if options.bot_config_file is not None else None
    bot_handlers = load_bot_handlers(available_bots, bots_config, third_party_bot_conf)
    message_handlers = init_message_handlers(available_bots, bots_lib_modules, bot_handlers)
    app.config["BOTS_LIB_MODULES"] = bots_lib_modules
    app.config["BOT_HANDLERS"] = bot_handlers
    app.config["MESSAGE_HANDLERS"] = message_handlers
    app.run(host=options.hostname, port=int(options.port), debug=True)

if __name__ == '__main__':
    main()

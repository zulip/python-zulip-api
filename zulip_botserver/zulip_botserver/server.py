import configparser
import os
import sys
import json
import argparse

from flask import Flask, request
from importlib import import_module
from typing import Any, Dict, Mapping, Union, List, Optional
from werkzeug.exceptions import BadRequest

from zulip import Client
from zulip_bots.custom_exceptions import ConfigValidationError
from zulip_bots.lib import ExternalBotHandler, StateHandler

bots_config = {}  # type: Dict[str, Mapping[str, str]]
available_bots = []  # type: List[str]
bots_lib_module = {}  # type: Dict[str, Any]
bot_handlers = {}  # type: Dict[str, ExternalBotHandler]

def read_config_file(config_file_path: str) -> None:
    config_file_path = os.path.abspath(os.path.expanduser(config_file_path))
    if not os.path.isfile(config_file_path):
        raise IOError("Could not read config file {}: File not found.".format(config_file_path))
    parser = configparser.ConfigParser()
    parser.read(config_file_path)

    for section in parser.sections():
        bots_config[section] = {
            "email": parser.get(section, 'email'),
            "key": parser.get(section, 'key'),
            "site": parser.get(section, 'site'),
        }

def load_lib_modules() -> None:
    for bot in available_bots:
        try:
            module_name = 'zulip_bots.bots.{bot}.{bot}'.format(bot=bot)
            lib_module = import_module(module_name)
            bots_lib_module[bot] = lib_module
        except ImportError:
            raise ImportError(
                "\n Import Error: Bot \"{}\" doesn't exists. Please make sure you have set up the flaskbotrc "
                "file correctly.\n".format(bot)
            )

def load_bot_handlers() -> Optional[BadRequest]:
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

            lib_module = get_bot_lib_module(bot)
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
    return None

def get_bot_lib_module(bot: str) -> Any:
    if bot in bots_lib_module.keys():
        return bots_lib_module[bot]
    return None

app = Flask(__name__)

@app.route('/bots/<bot>', methods=['POST'])
def handle_bot(bot: str) -> Union[str, BadRequest]:
    lib_module = get_bot_lib_module(bot)
    if lib_module is None:
        return BadRequest("Can't find the configuration or Bot Handler code for bot {}. "
                          "Make sure that the `zulip_bots` package is installed, and "
                          "that your flaskbotrc is set up correctly".format(bot))
    message_handler = lib_module.handler_class()

    event = request.get_json(force=True)
    message_handler.handle_message(message=event["message"],
                                   bot_handler=bot_handlers[bot])
    return json.dumps("")

def parse_args() -> argparse.Namespace:
    usage = '''
            zulip-bot-server --config-file <path to flaskbotrc> --hostname <address> --port <port>
            Example: zulip-bot-server --config-file ~/flaskbotrc
            (This program loads the bot configurations from the
            config file (flaskbotrc here) and loads the bot modules.
            It then starts the server and fetches the requests to the
            above loaded modules and returns the success/failure result)
            Please make sure you have a current flaskbotrc file with the
            configurations of the required bots.
            Hostname and Port are optional arguments. Default hostname is
            127.0.0.1 and default port is 5002.
            See lib/readme.md for more context.
            '''

    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument('--config-file',
                        action='store',
                        required=True,
                        help='Config file for the zulip bot server (flaskbotrc)')
    parser.add_argument('--hostname',
                        action='store',
                        default="127.0.0.1",
                        help='Address on which you want to run the server')
    parser.add_argument('--port',
                        action='store',
                        default=5002,
                        help='Port on which you want to run the server')
    return parser.parse_args()


def main() -> None:
    options = parse_args()
    read_config_file(options.config_file)
    global available_bots
    available_bots = list(bots_config.keys())
    load_lib_modules()
    load_bot_handlers()
    app.run(host=options.hostname, port=int(options.port), debug=True)

if __name__ == '__main__':
    main()

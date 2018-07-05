import configparser
import logging
import json
import os
import sys

from configparser import MissingSectionHeaderError, NoOptionError
from flask import Flask, request
from importlib import import_module
from typing import Any, Dict, Union, List, Optional
from werkzeug.exceptions import BadRequest, Unauthorized

from zulip import Client
from zulip_bots import lib
from zulip_botserver.input_parameters import parse_args


def read_config_section(parser: configparser.ConfigParser, section: str) -> Dict[str, str]:
    section_info = {
        "email": parser.get(section, 'email'),
        "key": parser.get(section, 'key'),
        "site": parser.get(section, 'site'),
        "token": parser.get(section, 'token'),
    }
    return section_info


def read_config_file(config_file_path: str, bot_name: Optional[str]=None) -> Dict[str, Dict[str, str]]:
    parser = parse_config_file(config_file_path)

    bots_config = {}  # type: Dict[str, Dict[str, str]]
    if bot_name is None:
        bots_config = {section: read_config_section(parser, section)
                       for section in parser.sections()}
        return bots_config

    logging.warning("Single bot mode is enabled")
    if len(parser.sections()) == 0:
        sys.exit("Error: Your Botserver config file `{0}` does not contain any sections!\n"
                 "You need to write the name of the bot you want to run in the "
                 "section header of `{0}`.".format(config_file_path))

    if bot_name in parser.sections():
        bot_section = bot_name
        bots_config[bot_name] = read_config_section(parser, bot_name)
        ignored_sections = [section for section in parser.sections() if section != bot_name]
    else:
        bot_section = parser.sections()[0]
        bots_config[bot_name] = read_config_section(parser, bot_section)
        logging.warning(
            "First bot name in the config list was changed from '{}' to '{}'".format(bot_section, bot_name)
        )
        ignored_sections = parser.sections()[1:]

    if len(ignored_sections) > 0:
        logging.warning("Sections except the '{}' will be ignored".format(bot_section))

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
            error_message = ("Error: Bot \"{}\" doesn't exist. Please make sure "
                             "you have set up the botserverrc file correctly.\n".format(bot))
            if bot == "api":
                error_message += "Did you forget to specify the bot you want to run with -b <botname> ?"
            sys.exit(error_message)
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
bots_config = {}  # type: Dict[str, Dict[str, str]]


@app.route('/', methods=['POST'])
def handle_bot() -> Union[str, BadRequest, Unauthorized]:
    event = request.get_json(force=True)
    for bot_name, config in bots_config.items():
        if config['email'] == event['bot_email']:
            bot = bot_name
            bot_config = config
            break
    else:
        return BadRequest("Cannot find a bot with email {} in the Botserver "
                          "configuration file. Do the emails in your botserverrc "
                          "match the bot emails on the server?".format(event['bot_email']))
    if bot_config['token'] != event['token']:
        return Unauthorized("Request token does not match token found for bot {} in the "
                            "Botserver configuration file. Do the outgoing webhooks in "
                            "Zulip point to the right Botserver?".format(event['bot_email']))
    lib_module = app.config.get("BOTS_LIB_MODULES", {})[bot]
    bot_handler = app.config.get("BOT_HANDLERS", {})[bot]
    message_handler = app.config.get("MESSAGE_HANDLERS", {})[bot]
    is_mentioned = event['trigger'] == "mention"
    is_private_message = event['trigger'] == "private_message"
    message = event["message"]
    message['full_content'] = message['content']
    # Strip at-mention botname from the message
    if is_mentioned:
        # message['content'] will be None when the bot's @-mention is not at the beginning.
        # In that case, the message shall not be handled.
        message['content'] = lib.extract_query_without_mention(message=message, client=bot_handler)
        if message['content'] is None:
            return json.dumps("")

    if is_private_message or is_mentioned:
        message_handler.handle_message(message=message, bot_handler=bot_handler)
    return json.dumps("")


def main() -> None:
    options = parse_args()
    global bots_config
    try:
        bots_config = read_config_file(options.config_file, options.bot_name)
    except MissingSectionHeaderError:
        sys.exit("Error: Your Botserver config file `{0}` contains an empty section header!\n"
                 "You need to write the names of the bots you want to run in the "
                 "section headers of `{0}`.".format(options.config_file))
    except NoOptionError as e:
        sys.exit("Error: Your Botserver config file `{0}` has a missing option `{1}` in section `{2}`!\n"
                 "You need to add option `{1}` with appropriate value in section `{2}` of `{0}`"
                 .format(options.config_file, e.option, e.section))

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

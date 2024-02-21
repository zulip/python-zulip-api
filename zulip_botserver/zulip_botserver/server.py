#!/usr/bin/env python3

import configparser
import json
import logging
import os
import sys
from collections import OrderedDict
from configparser import MissingSectionHeaderError, NoOptionError
from importlib import import_module
from types import ModuleType
from typing import Any, Dict, List, Optional

from flask import Flask, request
from werkzeug.exceptions import BadRequest, Unauthorized

from zulip import Client
from zulip_bots import lib
from zulip_bots.finder import import_module_from_source, import_module_from_zulip_bot_registry
from zulip_botserver.input_parameters import parse_args


def read_config_section(parser: configparser.ConfigParser, section: str) -> Dict[str, str]:
    section_info = {
        "email": parser.get(section, "email"),
        "key": parser.get(section, "key"),
        "site": parser.get(section, "site"),
        "token": parser.get(section, "token"),
    }
    return section_info


def read_config_from_env_vars(bot_name: Optional[str] = None) -> Dict[str, Dict[str, str]]:
    bots_config: Dict[str, Dict[str, str]] = {}
    json_config = os.environ.get("ZULIP_BOTSERVER_CONFIG")

    if json_config is None:
        raise OSError(
            "Could not read environment variable 'ZULIP_BOTSERVER_CONFIG': Variable not set."
        )

    # Load JSON-formatted environment variable; use OrderedDict to
    # preserve ordering on Python 3.6 and below.
    env_config = json.loads(json_config, object_pairs_hook=OrderedDict)
    if bot_name is not None:
        if bot_name in env_config:
            bots_config[bot_name] = env_config[bot_name]
        else:
            # If the bot name provided via the command line does not
            # exist in the configuration provided via the environment
            # variable, use the first bot in the environment variable,
            # with name updated to match, along with a warning.
            first_bot_name = next(iter(env_config.keys()))
            bots_config[bot_name] = env_config[first_bot_name]
            logging.warning(
                "First bot name in the config list was changed from %r to %r",
                first_bot_name,
                bot_name,
            )
    else:
        bots_config = dict(env_config)
    return bots_config


def read_config_file(
    config_file_path: str, bot_name: Optional[str] = None
) -> Dict[str, Dict[str, str]]:
    parser = parse_config_file(config_file_path)

    bots_config: Dict[str, Dict[str, str]] = {}
    if bot_name is None:
        bots_config = {
            section: read_config_section(parser, section) for section in parser.sections()
        }
        return bots_config

    logging.warning("Single bot mode is enabled")
    if len(parser.sections()) == 0:
        sys.exit(
            "Error: Your Botserver config file `{0}` does not contain any sections!\n"
            "You need to write the name of the bot you want to run in the "
            "section header of `{0}`.".format(config_file_path)
        )

    if bot_name in parser.sections():
        bot_section = bot_name
        bots_config[bot_name] = read_config_section(parser, bot_name)
        ignored_sections = [section for section in parser.sections() if section != bot_name]
    else:
        bot_section = parser.sections()[0]
        bots_config[bot_name] = read_config_section(parser, bot_section)
        logging.warning(
            "First bot name in the config list was changed from %r to %r", bot_section, bot_name
        )
        ignored_sections = parser.sections()[1:]

    if len(ignored_sections) > 0:
        logging.warning("Sections except the %r will be ignored", bot_section)

    return bots_config


def parse_config_file(config_file_path: str) -> configparser.ConfigParser:
    config_file_path = os.path.abspath(os.path.expanduser(config_file_path))
    if not os.path.isfile(config_file_path):
        raise OSError(f"Could not read config file {config_file_path}: File not found.")
    parser = configparser.ConfigParser()
    parser.read(config_file_path)
    return parser


def load_lib_modules(available_bots: List[str]) -> Dict[str, ModuleType]:
    bots_lib_module = {}
    for bot in available_bots:
        try:
            if bot.endswith(".py") and os.path.isfile(bot):
                lib_module = import_module_from_source(bot, "custom_bot_module")
            else:
                module_name = f"zulip_bots.bots.{bot}.{bot}"
                lib_module = import_module(module_name)
            bots_lib_module[bot] = lib_module
        except ImportError:
            _, bots_lib_module[bot] = import_module_from_zulip_bot_registry(bot)
            if bots_lib_module[bot] is None:
                error_message = (
                    f'Error: Bot "{bot}" doesn\'t exist. Please make sure '
                    "you have set up the botserverrc file correctly.\n"
                )
                if bot == "api":
                    error_message += (
                        "Did you forget to specify the bot you want to run with -b <botname> ?"
                    )
                sys.exit(error_message)
    return bots_lib_module


def load_bot_handlers(
    available_bots: List[str],
    bot_lib_modules: Dict[str, ModuleType],
    bots_config: Dict[str, Dict[str, str]],
    third_party_bot_conf: Optional[configparser.ConfigParser] = None,
) -> Dict[str, lib.ExternalBotHandler]:
    bot_handlers = {}
    for bot in available_bots:
        client = Client(
            email=bots_config[bot]["email"],
            api_key=bots_config[bot]["key"],
            site=bots_config[bot]["site"],
        )
        bot_file = bot_lib_modules[bot].__file__
        assert bot_file is not None
        bot_dir = os.path.dirname(os.path.abspath(bot_file))
        bot_handler = lib.ExternalBotHandler(
            client, bot_dir, bot_details={}, bot_config_parser=third_party_bot_conf
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
bots_config: Dict[str, Dict[str, str]] = {}


@app.route("/", methods=["POST"])
def handle_bot() -> str:
    event = request.get_json(force=True)
    assert event is not None
    for bot_name, config in bots_config.items():
        if config["email"] == event["bot_email"]:
            bot = bot_name
            bot_config = config
            break
    else:
        raise BadRequest(
            "Cannot find a bot with email {} in the Botserver "
            "configuration file. Do the emails in your botserverrc "
            "match the bot emails on the server?".format(event["bot_email"])
        )
    if bot_config["token"] != event["token"]:
        raise Unauthorized(
            "Request token does not match token found for bot {} in the "
            "Botserver configuration file. Do the outgoing webhooks in "
            "Zulip point to the right Botserver?".format(event["bot_email"])
        )
    app.config.get("BOTS_LIB_MODULES", {})[bot]
    bot_handler = app.config.get("BOT_HANDLERS", {})[bot]
    message_handler = app.config.get("MESSAGE_HANDLERS", {})[bot]
    is_mentioned = event["trigger"] == "mention"
    # TODO/compatibility: Remove the support for "private_message" as a valid
    # trigger value once we no longer support pre-8.0 Zulip servers.
    is_direct_message = event["trigger"] in ["direct_message", "private_message"]
    message = event["message"]
    message["full_content"] = message["content"]
    # Strip at-mention botname from the message
    if is_mentioned:
        # message['content'] will be None when the bot's @-mention is not at the beginning.
        # In that case, the message shall not be handled.
        message["content"] = lib.extract_query_without_mention(message=message, client=bot_handler)
        if message["content"] is None:
            return json.dumps(dict(response_not_required=True))

    if is_direct_message or is_mentioned:
        message_handler.handle_message(message=message, bot_handler=bot_handler)
    return json.dumps(dict(response_not_required=True))


def main() -> None:
    options = parse_args()
    global bots_config  # noqa: PLW0603

    if options.use_env_vars:
        bots_config = read_config_from_env_vars(options.bot_name)
    elif options.config_file:
        try:
            bots_config = read_config_file(options.config_file, options.bot_name)
        except MissingSectionHeaderError:
            sys.exit(
                "Error: Your Botserver config file `{0}` contains an empty section header!\n"
                "You need to write the names of the bots you want to run in the "
                "section headers of `{0}`.".format(options.config_file)
            )
        except NoOptionError as e:
            sys.exit(
                "Error: Your Botserver config file `{0}` has a missing option `{1}` in section `{2}`!\n"
                "You need to add option `{1}` with appropriate value in section `{2}` of `{0}`".format(
                    options.config_file, e.option, e.section
                )
            )

    available_bots = list(bots_config.keys())
    bots_lib_modules = load_lib_modules(available_bots)
    third_party_bot_conf = (
        parse_config_file(options.bot_config_file) if options.bot_config_file is not None else None
    )
    bot_handlers = load_bot_handlers(
        available_bots, bots_lib_modules, bots_config, third_party_bot_conf
    )
    message_handlers = init_message_handlers(available_bots, bots_lib_modules, bot_handlers)
    app.config["BOTS_LIB_MODULES"] = bots_lib_modules
    app.config["BOT_HANDLERS"] = bot_handlers
    app.config["MESSAGE_HANDLERS"] = message_handlers
    app.run(host=options.hostname, port=int(options.port))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from typing import Optional

import zulip
from zulip_bots import finder
from zulip_bots.lib import (
    NoBotConfigError,
    run_message_handler_for_bot,
)
from zulip_bots.provision import provision_bot

current_dir = os.path.dirname(os.path.abspath(__file__))


def parse_args() -> argparse.Namespace:
    usage = """
        zulip-run-bot <bot> --config-file ~/zuliprc
        zulip-run-bot --help
        """

    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument("bot", action="store", help="the name or path of an existing bot to run")

    parser.add_argument("--quiet", "-q", action="store_true", help="turn off logging output")

    parser.add_argument(
        "--config-file",
        "-c",
        action="store",
        help="zulip configuration file (e.g. ~/Downloads/zuliprc)",
    )

    parser.add_argument(
        "--bot-config-file",
        "-b",
        action="store",
        help="third party configuration file (e.g. ~/giphy.conf",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="try running the bot even if dependencies install fails",
    )

    parser.add_argument(
        "--registry",
        "-r",
        action="store_true",
        help="run the bot via zulip_bots registry",
    )

    parser.add_argument("--provision", action="store_true", help="install dependencies for the bot")

    args = parser.parse_args()
    return args


def exit_gracefully_if_zulip_config_is_missing(config_file: Optional[str]) -> None:
    zulip.exit_gracefully_if_zulip_config_is_missing(config_file, allow_default_config=False)


def exit_gracefully_if_bot_config_file_does_not_exist(bot_config_file: Optional[str]) -> None:
    if bot_config_file is None:
        # This is a common case, just so succeed quietly. (Some
        # bots don't have third party configuration.)
        return

    if not os.path.exists(bot_config_file):
        print(
            f"""
            ERROR: {bot_config_file} does not exist.

            You probably just specified the wrong file location here.
            """
        )
        sys.exit(1)


def main() -> None:
    args = parse_args()

    if args.registry:
        try:
            bot_source, lib_module = finder.import_module_from_zulip_bot_registry(args.bot)
        except finder.DuplicateRegisteredBotNameError as error:
            print(
                f'ERROR: Found duplicate entries for "{error}" in zulip bots registry.\n'
                "Make sure that you don't install bots using the same entry point. Exiting now."
            )
            sys.exit(1)
        if lib_module:
            bot_name = args.bot
    else:
        result = finder.resolve_bot_path(args.bot)
        if result:
            bot_path, bot_name = result
            sys.path.insert(0, os.path.dirname(bot_path))

            if args.provision:
                provision_bot(os.path.dirname(bot_path), args.force)

            try:
                lib_module = finder.import_module_from_source(bot_path.as_posix(), bot_name)
            except ImportError:
                req_path = os.path.join(os.path.dirname(bot_path), "requirements.txt")
                with open(req_path) as fp:
                    deps_list = fp.read()

                dep_err_msg = (
                    "ERROR: The following dependencies for the {bot_name} bot are not installed:\n\n"
                    "{deps_list}\n"
                    "If you'd like us to install these dependencies, run:\n"
                    "    zulip-run-bot {bot_name} --provision"
                )
                print(dep_err_msg.format(bot_name=bot_name, deps_list=deps_list))
                sys.exit(1)
            bot_source = "source"
        else:
            lib_module = finder.import_module_by_name(args.bot)
            if lib_module:
                bot_name = lib_module.__name__
                bot_source = "named module"
                if args.provision:
                    print("ERROR: Could not load bot's module for '{}'. Exiting now.")
                    sys.exit(1)

    if lib_module is None:
        print("ERROR: Could not load bot module. Exiting now.")
        sys.exit(1)

    if not args.quiet:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    # It's a bit unfortunate that we have two config files, but the
    # alternative would be way worse for people running multiple bots
    # or testing against multiple Zulip servers.
    exit_gracefully_if_zulip_config_is_missing(args.config_file)
    exit_gracefully_if_bot_config_file_does_not_exist(args.bot_config_file)

    try:
        run_message_handler_for_bot(
            lib_module=lib_module,
            config_file=args.config_file,
            bot_config_file=args.bot_config_file,
            quiet=args.quiet,
            bot_name=bot_name,
            bot_source=bot_source,
        )
    except NoBotConfigError:
        print(
            """
            ERROR: Your bot requires you to specify a third party
            config file with the --bot-config-file option.

            Exiting now.
            """
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import logging
import argparse
import sys
import os
from os.path import basename, splitext

from typing import Any, Optional, Text

from zulip_bots.lib import (
    run_message_handler_for_bot,
    NoBotConfigException,
)

from zulip_bots.provision import provision_bot

current_dir = os.path.dirname(os.path.abspath(__file__))


def import_module_from_source(path: Text, name: Optional[Text]=None) -> Any:
    if not name:
        name = splitext(basename(path))[0]

    # importlib.util.module_from_spec is supported from Python3.5
    py_version = sys.version_info
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 5):
        import imp
        module = imp.load_source(name, path)
    else:
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        loader = spec.loader
        if loader is None:
            return None
        loader.exec_module(module)

    return module


def parse_args() -> argparse.Namespace:
    usage = '''
        zulip-run-bot <bot_name> --config-file ~/zuliprc
        zulip-run-bot --help
        '''

    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument('bot',
                        action='store',
                        help='the name or path of an existing bot to run')

    parser.add_argument('--quiet', '-q',
                        action='store_true',
                        help='turn off logging output')

    parser.add_argument('--config-file', '-c',
                        action='store',
                        required=True,
                        help='zulip configuration file (e.g. ~/Downloads/zuliprc)')

    parser.add_argument('--bot-config-file', '-b',
                        action='store',
                        help='third party configuration file (e.g. ~/giphy.conf')

    parser.add_argument('--force',
                        action='store_true',
                        help='try running the bot even if dependencies install fails')

    parser.add_argument('--provision',
                        action='store_true',
                        help='install dependencies for the bot')

    args = parser.parse_args()
    return args


def exit_gracefully_if_zulip_config_file_does_not_exist(config_file: str) -> None:
    if not os.path.exists(config_file):
        print('''
            ERROR: %s does not exist.

            You may need to download a config file from the Zulip app, or
            if you have already done that, you need to specify the file
            location correctly.
            ''' % (config_file,))
        sys.exit(1)


def exit_gracefully_if_bot_config_file_does_not_exist(bot_config_file: str) -> None:
    if bot_config_file is None:
        # This is a common case, just so succeed quietly. (Some
        # bots don't have third party configuration.)
        return

    if not os.path.exists(bot_config_file):
        print('''
            ERROR: %s does not exist.

            You probably just specified the wrong file location here.
            ''' % (bot_config_file,))
        sys.exit(1)


def main() -> None:
    args = parse_args()
    if os.path.isfile(args.bot):
        bot_path = os.path.abspath(args.bot)
        bot_name = os.path.splitext(basename(bot_path))[0]
    else:
        bot_path = os.path.abspath(os.path.join(current_dir, 'bots', args.bot, args.bot+'.py'))
        bot_name = args.bot
    sys.path.insert(0, os.path.dirname(bot_path))
    if args.provision:
        provision_bot(os.path.dirname(bot_path), args.force)

    lib_module = import_module_from_source(bot_path, bot_name)
    if lib_module is None:
        print("ERROR: Could not load bot module. Exiting now.")
        sys.exit(1)

    if not args.quiet:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    # It's a bit unfortunate that we have two config files, but the
    # alternative would be way worse for people running multiple bots
    # or testing against multiple Zulip servers.
    exit_gracefully_if_zulip_config_file_does_not_exist(args.config_file)
    exit_gracefully_if_bot_config_file_does_not_exist(args.bot_config_file)

    try:
        run_message_handler_for_bot(
            lib_module=lib_module,
            config_file=args.config_file,
            bot_config_file=args.bot_config_file,
            quiet=args.quiet,
            bot_name=bot_name
        )
    except NoBotConfigException:
        print('''
            ERROR: Your bot requires you to specify a third party
            config file with the --bot-config-file option.

            Exiting now.
            ''')
        sys.exit(1)

if __name__ == '__main__':
    main()

#!/usr/bin/env python
from __future__ import print_function
from __future__ import absolute_import

import logging
import optparse
import sys
from types import ModuleType
from importlib import import_module
from os.path import basename, splitext

import six

from zulip_bots.lib import run_message_handler_for_bot


def import_module_from_source(path, name=None):
    if name is None:
        name = splitext(basename(path))[0]

    if six.PY2:
        import imp
        module = imp.load_source(name, path)
        return module
    else:
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def parse_args():
    usage = '''
        zulip-run-bot <bot_name>
        Example: zulip-run-bot followup
        (This program loads bot-related code from the
        library code and then runs a message loop,
        feeding messages to the library code to handle.)
        Please make sure you have a current ~/.zuliprc
        file with the credentials you want to use for
        this bot.
        See lib/readme.md for more context.
        '''

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--quiet', '-q',
                      action='store_true',
                      help='Turn off logging output.')

    parser.add_option('--config-file',
                      action='store',
                      help='(alternate config file to ~/.zuliprc)')

    parser.add_option('--path-to-bot',
                      action='store',
                      help='path to the file with the bot handler class')

    parser.add_option('--force',
                      action='store_true',
                      help='Try running the bot even if dependencies install fails.')
    (options, args) = parser.parse_args()

    if not args and not options.path_to_bot:
        error_message = """
You must either specify the name of an existing bot or
specify a path to the file (--path-to-bot) that contains
the bot handler class.
"""
        parser.error(error_message)

    return (options, args)


def main():
    # type: () -> None
    (options, args) = parse_args()

    bot_name = None
    if args:
        bot_name = args[0]

    if options.path_to_bot:
        lib_module = import_module_from_source(options.path_to_bot, name=bot_name)
    else:
        lib_module = import_module('zulip_bots.bots.{bot}.{bot}'.format(bot=bot_name))

    if not options.quiet:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    run_message_handler_for_bot(
        lib_module=lib_module,
        config_file=options.config_file,
        quiet=options.quiet
    )

if __name__ == '__main__':
    main()

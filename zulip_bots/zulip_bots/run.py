#!/usr/bin/env python
from __future__ import print_function
from __future__ import absolute_import

import logging
import optparse
import sys
from types import ModuleType
from importlib import import_module

from zulip_bots.lib import run_message_handler_for_bot


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

    parser.add_option('--force',
                      action='store_true',
                      help='Try running the bot even if dependencies install fails.')
    (options, args) = parser.parse_args()
    if not args:
        parser.error('You must specify the name of the bot!')

    return (options, args)


def main():
    # type: () -> None
    (options, args) = parse_args()
    bot_name = args[0]

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

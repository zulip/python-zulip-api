#!/usr/bin/env python
from __future__ import print_function
from __future__ import absolute_import

import argparse
import sys
import os
from types import ModuleType
from importlib import import_module
from os.path import basename, splitext

import six
from six.moves import configparser
import mock
from mock import MagicMock, patch

from zulip_bots.lib import run_message_handler_for_bot, StateHandler
from zulip_bots.provision import provision_bot
from zulip_bots.run import import_module_from_source, name_and_patch_match

def parse_args():
    usage = '''
        zulip-bot-output <bot_name> --message "Send this message to the bot"
        Example: zulip-bot-output xkcd --message "1"
        This tool can be used for testing bots by sending simple messages
        and capturing the response.
        (Internally, this program loads bot-related code from the
        library code and then feeds the message provided
        in the command to the library code to handle.)
        '''

    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument('name',
                        action='store',
                        nargs='?',
                        default=None,
                        help='the name of an existing bot to run')
    parser.add_argument('--message',
                        action='store',
                        help='the message content to send to the bot')

    parser.add_argument('--path-to-bot',
                        action='store',
                        help='path to the file with the bot handler class')

    parser.add_argument('--force',
                        action='store_true',
                        help='Try running the bot even if dependencies install fails.')

    parser.add_argument('--provision',
                        action='store_true',
                        help='Install dependencies for the bot.')

    options = parser.parse_args()

    if not options.name and not options.path_to_bot:
        error_message = """
You must either specify the name of an existing bot or
specify a path to the file (--path-to-bot) that contains
the bot handler class.
"""
        parser.error(error_message)
    # Checks if both name and path to bots are provided:
    # checks if both of these are in sync, otherwise we'll
    # have to be bias towards one and the user may get incorrect
    # result.
    elif not name_and_patch_match(options.name, options.path_to_bot):
        error_message = """
Please make sure that the given name of the bot and the
given path to the bot are same and valid.
"""
        parser.error(error_message)

    return options

def main():
    # type: () -> None
    options = parse_args()
    bot_name = options.name
    if options.path_to_bot:
        if options.provision:
            bot_dir = os.path.dirname(os.path.abspath(options.path_to_bot))
            provision_bot(bot_dir, options.force)
        lib_module = import_module_from_source(options.path_to_bot, name=bot_name)
    elif options.name:
        if options.provision:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            bots_parent_dir = os.path.join(current_dir, "bots")
            bot_dir = os.path.join(bots_parent_dir, options.name)
            provision_bot(bot_dir, options.force)
        lib_module = import_module('zulip_bots.bots.{bot}.{bot}'.format(bot=bot_name))

    message = {'content': options.message, 'sender_email': 'foo_sender@zulip.com'}
    message_handler = lib_module.handler_class()

    with patch('zulip_bots.lib.ExternalBotHandler') as mock_bot_handler:
        def get_config_info(bot_name, section=None, optional=False):
            # type: (str, Optional[str], Optional[bool]) -> Dict[str, Any]
            conf_file_path = os.path.realpath(os.path.join(
                'zulip_bots', 'bots', bot_name, bot_name + '.conf'))
            section = section or bot_name
            config = configparser.ConfigParser()
            try:
                with open(conf_file_path) as conf:
                    config.readfp(conf)  # type: ignore
            except IOError:
                if optional:
                    return dict()
                raise
            return dict(config.items(section))

        mock_bot_handler.get_config_info = get_config_info
        if hasattr(message_handler, 'initialize') and callable(message_handler.initialize):
            message_handler.initialize(mock_bot_handler)

        mock_bot_handler.send_reply = MagicMock()
        mock_bot_handler.send_message = MagicMock()
        message_handler.handle_message(
            message=message,
            bot_handler=mock_bot_handler,
            state_handler=StateHandler()
        )
        print("On sending ", options.name, " bot the following message:\n\"", options.message, "\"")

        # send_reply and send_message have slightly arguments; the
        # following takes that into account.
        #   send_reply(original_message, response)
        #   send_message(response_message)
        if mock_bot_handler.send_reply.called:
            print("\nThe bot gives the following output message:\n\"", list(mock_bot_handler.send_reply.call_args)[0][1], "\"")
        elif mock_bot_handler.send_message.called:
            print("\nThe bot sends the following output to zulip:\n\"", list(mock_bot_handler.send_message.call_args)[0][0], "\"")
        else:
            print("\nThe bot sent no reply.")

if __name__ == '__main__':
    main()

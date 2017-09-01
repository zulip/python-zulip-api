#!/usr/bin/env python
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import argparse
import zulip_bots

from six.moves import configparser

from mock import MagicMock, patch
from zulip_bots.lib import StateHandler
from zulip_bots.lib import ExternalBotHandler
from zulip_bots.provision import provision_bot
from zulip_bots.run import import_module_from_source

current_dir = os.path.dirname(os.path.abspath(__file__))

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
    parser.add_argument('bot',
                        action='store',
                        help='the name or path an existing bot to run')

    parser.add_argument('--message', '-m',
                        action='store',
                        help='the message content to send to the bot')

    parser.add_argument('--force', '-f',
                        action='store_true',
                        help='try running bot even if dependencies install fails')

    parser.add_argument('--provision', '-p',
                        action='store_true',
                        help='install dependencies for the bot')

    args = parser.parse_args()
    return args

def main():
    # type: () -> None
    args = parse_args()
    if os.path.isfile(args.bot):
        bot_path = os.path.abspath(args.bot)
        bot_name = os.path.splitext(os.path.basename(bot_path))[0]
    else:
        bot_path = os.path.abspath(os.path.join(current_dir, 'bots', args.bot, args.bot+'.py'))
        bot_name = args.bot
    bot_dir = os.path.dirname(bot_path)
    if args.provision:
        provision_bot(os.path.dirname(bot_path), args.force)
    lib_module = import_module_from_source(bot_path, bot_name)

    message = {'content': args.message, 'sender_email': 'foo_sender@zulip.com'}
    message_handler = lib_module.handler_class()

    with patch('zulip.Client') as mock_client:
        mock_bot_handler = ExternalBotHandler(mock_client, bot_dir)
        mock_bot_handler.send_reply = MagicMock()
        mock_bot_handler.send_message = MagicMock()
        mock_bot_handler.update_message = MagicMock()
        if hasattr(message_handler, 'initialize') and callable(message_handler.initialize):
            message_handler.initialize(mock_bot_handler)
        message_handler.handle_message(
            message=message,
            bot_handler=mock_bot_handler,
            state_handler=StateHandler()
        )
        print("On sending ", bot_name, " bot the following message:\n\"", args.message, "\"")

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

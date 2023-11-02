#!/usr/bin/env python3
import argparse
import os
import sys

from zulip_bots.finder import import_module_from_source, resolve_bot_path
from zulip_bots.simple_lib import MockMessageServer, TerminalBotHandler

current_dir = os.path.dirname(os.path.abspath(__file__))


def parse_args() -> argparse.Namespace:
    description = """
        This tool allows you to test a bot using the terminal (and no Zulip server).

        Examples:   %(prog)s followup
        """

    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("bot", action="store", help="the name or path an existing bot to run")

    parser.add_argument(
        "--bot-config-file",
        "-b",
        action="store",
        help="optional third party config file (e.g. ~/giphy.conf)",
    )

    args = parser.parse_args()
    return args


def main() -> None:
    args = parse_args()

    # NOTE: Use of only this implies bots from eg. registry cannot be explored in this way
    result = resolve_bot_path(args.bot)
    if result is None:
        print(f"Cannot find find and import bot '{args.bot}'")
        sys.exit(1)

    bot_path, bot_name = result
    bot_dir = os.path.dirname(bot_path)
    sys.path.insert(0, bot_dir)

    lib_module = import_module_from_source(bot_path.as_posix(), bot_name)
    if lib_module is None:
        print(f"Could not find and import bot '{bot_name}'")
        sys.exit(1)

    try:
        message_handler = lib_module.handler_class()
    except AttributeError:
        print("This module does not appear to have a bot handler_class specified.")
        sys.exit(1)

    message_server = MockMessageServer()
    bot_handler = TerminalBotHandler(args.bot_config_file, message_server)
    if hasattr(message_handler, "initialize") and callable(message_handler.initialize):
        message_handler.initialize(bot_handler)

    sender_email = "foo_sender@zulip.com"

    try:
        while True:
            content = input("Enter your message: ")

            message = message_server.send(
                dict(
                    content=content,
                    sender_email=sender_email,
                    display_recipient=sender_email,
                )
            )

            message_handler.handle_message(
                message=message,
                bot_handler=bot_handler,
            )
    except KeyboardInterrupt:
        print(
            "\n\nOk, if you're happy with your terminal-based testing, try it out with a Zulip server.",
            "\nYou can refer to https://zulip.com/api/running-bots#running-a-bot.",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

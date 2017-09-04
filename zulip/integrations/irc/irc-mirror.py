#!/usr/bin/env python
#
# EXPERIMENTAL
# IRC <=> Zulip mirroring bot
#
# Setup: First, you need to install python-irc version 8.5.3
# (https://github.com/jaraco/irc)

from __future__ import print_function
import zulip
import argparse

from irc_mirror_backend import IRCBot

if False:
    from typing import Any, Dict

usage = """./irc-mirror.py --irc-server=IRC_SERVER --channel=<CHANNEL> --nick-prefix=<NICK> [optional args]

Example:

./irc-mirror.py --irc-server=127.0.0.1 --channel='#test' --nick-prefix=username

Specify your Zulip API credentials and server in a ~/.zuliprc file or using the options.

Note that "_zulip" will be automatically appended to the IRC nick provided

Also note that at present you need to edit this code to do the Zulip => IRC side

"""


if __name__ == "__main__":
    parser = zulip.add_default_arguments(argparse.ArgumentParser(usage=usage))
    parser.add_argument('--irc-server', default=None)
    parser.add_argument('--port', default=6667)
    parser.add_argument('--nick-prefix', default=None)
    parser.add_argument('--channel', default=None)

    options = parser.parse_args()

    if options.irc_server is None or options.nick_prefix is None or options.channel is None:
        parser.error("Missing required argument")

    # Setting the client to irc_mirror is critical for this to work
    options.client = "irc_mirror"
    zulip_client = zulip.init_from_options(options)

    nickname = options.nick_prefix + "_zulip"
    bot = IRCBot(zulip_client, options.channel, nickname, options.irc_server, options.port)
    bot.start()

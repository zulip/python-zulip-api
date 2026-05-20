#!/usr/bin/env python3
#
# EXPERIMENTAL
# IRC <=> Zulip mirroring bot
#

import argparse
import configparser
import sys
import traceback
from typing import Tuple

import zulip

usage = """./irc-mirror.py --config irc_mirror.conf
"""


class BridgeConfigError(Exception):
    pass


def read_configuration(
    config_file: str,
) -> Tuple[configparser.SectionProxy, configparser.SectionProxy]:
    config: configparser.ConfigParser = configparser.ConfigParser()
    config.read(config_file)

    config_irc = config["irc"]
    for required in ["host", "port", "nickname", "channel"]:
        if required not in config_irc:
            raise BridgeConfigError(f"Missing required configuration: {required}")
    config_zulip = config["api"]
    for required in ["stream", "topic"]:
        if required not in config_zulip:
            raise BridgeConfigError(f"Missing required configuration: {required}")

    return config_irc, config_zulip


if __name__ == "__main__":
    parser = zulip.add_default_arguments(
        argparse.ArgumentParser(usage=usage), allow_provisioning=True
    )
    parser.add_argument(
        "-c", "--config", required=False, help="Path to the config file for the bridge."
    )

    options = parser.parse_args()
    # Setting the client to irc_mirror is critical for this to work
    options.client = "irc_mirror"
    zulip_client = zulip.Client(config_file=options.config)
    try:
        from irc_mirror_backend import IRCBot
    except ImportError:
        traceback.print_exc()
        print(
            "You have unsatisfied dependencies. Install all missing dependencies with "
            f"{sys.argv[0]} --provision"
        )
        sys.exit(1)

    config_irc, config_zulip = read_configuration(options.config)

    bot = IRCBot(
        zulip_client,
        config_zulip["stream"],
        config_zulip["topic"],
        config_irc["channel"],
        config_irc["nickname"],
        config_irc["host"],
        config_irc.get("nickserv_password", ""),
        int(config_irc["port"]),
        sasl_password=config_irc.get("sasl_password", None),
    )
    bot.start()

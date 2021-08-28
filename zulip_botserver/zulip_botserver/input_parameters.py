import argparse


def parse_args() -> argparse.Namespace:
    usage = """
        zulip-botserver --config-file <path/to/botserverrc> [--hostname=<address>] [--port=<port>]
    """

    parser = argparse.ArgumentParser(usage=usage)
    mutually_exclusive_args = parser.add_mutually_exclusive_group(required=True)
    # config-file or use-env-vars made mutually exclusive to prevent conflicts
    mutually_exclusive_args.add_argument(
        "--config-file",
        "-c",
        action="store",
        help="Config file for the Botserver. Use your `botserverrc` for multiple bots or"
        "`zuliprc` for a single bot.",
    )
    mutually_exclusive_args.add_argument(
        "--use-env-vars",
        "-e",
        action="store_true",
        help="Load configuration from JSON in ZULIP_BOTSERVER_CONFIG environment variable.",
    )
    parser.add_argument(
        "--bot-config-file",
        action="store",
        default=None,
        help="Config file for bots. Only needed when one of "
        "the bots you want to run requires a config file.",
    )
    parser.add_argument(
        "--bot-name",
        "-b",
        action="store",
        help="Run a single bot BOT_NAME. Use this option to run the Botserver "
        "with a `zuliprc` config file.",
    )
    parser.add_argument(
        "--hostname",
        action="store",
        default="127.0.0.1",
        help="Address on which you want to run the Botserver. (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        action="store",
        default=5002,
        type=int,
        help="Port on which you want to run the Botserver. (default: %(default)d)",
    )
    return parser.parse_args()

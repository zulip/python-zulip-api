import argparse


def parse_args() -> argparse.Namespace:
    usage = '''
        zulip-bot-server --config-file <path to flaskbotrc> --hostname <address> --port <port>
        Example1: zulip-bot-server --config-file ~/flaskbotrc
        Example2: zulip-bot-server --config-file ~/flaskbotrc -b mybotname
        (This program loads the bot configurations from the
        config file (flaskbotrc here) and loads the bot modules.
        It then starts the server and fetches the requests to the
        above loaded modules and returns the success/failure result)
        Please make sure you have a current flaskbotrc file with the
        configurations of the required bots.
        Hostname and Port are optional arguments. Default hostname is
        127.0.0.1 and default port is 5002.
        See lib/readme.md for more context.
    '''

    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument(
        '--config-file',
        action='store',
        required=True,
        help='Config file for the zulip bot server (flaskbotrc)'
    )
    parser.add_argument(
        '--bot-config-file',
        action='store',
        default=None,
        help='Config file for third-party bots'
    )
    parser.add_argument(
        '--bot-name', '-b',
        action='store',
        help='Bot name (optional, rewrites first bot name from config file). '
             'Only for single-bot usage! Other bots will be ignored'
    )
    parser.add_argument(
        '--hostname',
        action='store',
        default="127.0.0.1",
        help='Address on which you want to run the server'
    )
    parser.add_argument(
        '--port',
        action='store',
        default=5002,
        type=int,
        help='Port on which you want to run the server'
    )
    return parser.parse_args()

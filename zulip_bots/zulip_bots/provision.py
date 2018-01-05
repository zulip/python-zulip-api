#!/usr/bin/env python3

from __future__ import absolute_import

import argparse
import logging
import os
import sys
import glob
import pip
from typing import Iterator

def get_bot_paths():
    # type: () -> Iterator[str]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    bots_dir = os.path.join(current_dir, "bots")
    bots_subdirs = map(lambda d: os.path.abspath(d), glob.glob(bots_dir + '/*'))
    paths = filter(lambda d: os.path.isdir(d), bots_subdirs)
    return paths

def provision_bot(path_to_bot, force):
    # type: (str, bool) -> None
    req_path = os.path.join(path_to_bot, 'requirements.txt')
    if os.path.isfile(req_path):
        bot_name = os.path.basename(path_to_bot)
        logging.info('Installing dependencies for {}...'.format(bot_name))

        # pip install -r $BASEDIR/requirements.txt -t $BASEDIR/bot_dependencies --quiet
        rcode = pip.main(['install', '-r', req_path, '--quiet'])

        if rcode != 0:
            logging.error('Error. Check output of `pip install` above for details.')
            if not force:
                logging.error('Use --force to try running anyway.')
                sys.exit(rcode)  # Use pip's exit code
        else:
            logging.info('Installed dependencies successfully.')


def parse_args(available_bots):
    # type: (Iterator[str]) -> argparse.Namespace
    usage = """
Installs dependencies of bots in the bots/<bot_name>
directories. Add a requirements.txt file in a bot's folder
before provisioning.

To provision all bots, use:
./provision.py

To provision specific bots, use:
./provision.py [names of bots]
Example: ./provision.py helloworld xkcd wikipedia
"""
    parser = argparse.ArgumentParser(usage=usage)

    parser.add_argument('bots_to_provision',
                        metavar='bots',
                        nargs='*',
                        default=available_bots,
                        help='specific bots to provision (default is all)')

    parser.add_argument('--force',
                        default=False,
                        action="store_true",
                        help='Continue installation despite pip errors.')

    parser.add_argument('--quiet', '-q',
                        action='store_true',
                        default=False,
                        help='Turn off logging output.')

    return parser.parse_args()


def main():
    # type: () -> None
    options = parse_args(available_bots=get_bot_paths())

    if not options.quiet:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    for bot in options.bots_to_provision:
        provision_bot(bot, options.force)

if __name__ == '__main__':
    main()

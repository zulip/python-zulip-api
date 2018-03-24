#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# An easy Trello integration for Zulip.


from __future__ import absolute_import

import sys
import argparse
import requests

# Import configuration
import zulip_trello_config as configuration


VERSION = '0.2'


# argument's settings
parser = argparse.ArgumentParser()

parser.add_argument(
    'stream_name',
    help='The stream to which to integrate Trello.'
)

parser.add_argument(
    'trello_board_name',
    help='The Trello board name.'
)

parser.add_argument(
    'trello_board_id',
    help='The Trello board short id.'
)

parser.add_argument(
    '-v',
    '--version',
    help='Display Version and exit',
    action='version',
    version='zulip_trello v'+VERSION
)


def check_configuration() -> bool:
    """check_configuration

    Check if configuration fields have been populated in
    zulip_trello_config.py

    :returns: config imported from module zulip_trello_config

    """

    errors = []

    if not configuration.BOT_API_KEY:
        errors.append('Error: BOT_API_KEY is not defined in zulip_trello_config.py')

    if not configuration.TRELLO_API_KEY:
        errors.append('Error: TRELLO_API_KEY is not defined in zulip_trello_config.py')

    if not configuration.TRELLO_TOKEN:
        errors.append('Error: TRELLO_TOKEN is not defined in zulip_trello_config.py')

    if not configuration.ZULIP_HOST:
        errors.append('Error: ZULIP_HOST is not defined in zulip_trello_config.py')

    if len(errors) > 0:
        for error in errors:
            print(error)

        sys.exit(1)

    return True


def get_model_id(options: argparse.Namespace) -> str:
    """get_model_id

    Get Model Id from Trello API

    :options: argparse.Namespace arguments

    :returns: str id_model Trello board idModel

    """

    trello_api_url = 'https://api.trello.com/1/board/%s' % (
        options.trello_board_id
    )

    params = {
        'key': configuration.TRELLO_API_KEY,
        'token': configuration.TRELLO_TOKEN,
    }

    trello_response = requests.get(
        trello_api_url,
        params=params
    )

    if trello_response.status_code is not 200:
        print('Error: Can\'t get the idModel. Please check the configuration')
        sys.exit(1)

    board_info_json = trello_response.json()

    return board_info_json['id']


def get_webhook_id(options: argparse.Namespace, id_model: str) -> str:
    """get_webhook_id

    Get webhook id from Trello API

    :options: argparse.Namespace arguments
    :id_model: str Trello board idModel

    :returns: str id_webhook Trello webhook id

    """

    trello_api_url = 'https://api.trello.com/1/webhooks/'

    data = {
        'key': configuration.TRELLO_API_KEY,
        'token': configuration.TRELLO_TOKEN,
        'description': 'Webhook for Zulip integration (From Trello %s to Zulip %s)' % (
            options.trello_board_name,
            options.stream_name
        ),
        'callbackURL': '%s' % (
            'https://%s/api/v1/external/trello?api_key=%s&stream=%s' % (
                configuration.ZULIP_HOST,
                configuration.BOT_API_KEY,
                options.stream_name
            ),
        ),
        'idModel': id_model
    }

    trello_response = requests.post(
        trello_api_url,
        data=data
    )

    if trello_response.status_code is not 200:
        print('Error: Can\'t create the Webhook:', trello_response.text)
        sys.exit(1)

    webhook_info_json = trello_response.json()

    return webhook_info_json['id']


def log_webhook_info(options: argparse.Namespace, id_webhook: str) -> bool:
    """log_webhook_info

    Log webhook info in csv file for possible future use

    :options: argparse.Namespace arguments
    :id_webhook: str Trello webhook id

    :returns: bool

    """

    with open('zulip_trello_webhooks.csv', 'a') as webhooks_file:
        webhooks_file.write(
            '%s,%s,%s\n' % (
                options.stream_name,
                options.trello_board_name,
                id_webhook
            )
        )

    return True


def create_webhook(options: argparse.Namespace) -> bool:
    """create_webhook

    Create Trello webhook

    :options: argparse.Namespace arguments

    :returns: bool

    """

    # first, we need to get the idModel
    print('Getting Trello idModel for the %s board...' % (options.trello_board_name))

    id_model = get_model_id(options)

    if id_model:
        print('Success! The idModel is', id_model)

    # Next, we need to create the webhook
    print('Creating the webhook for the %s stream...' % (options.stream_name))

    id_webhook = get_webhook_id(options, id_model)

    if id_webhook:
        print('Success! The webhook id is', id_webhook)

    # The webhook was successfully created,
    # Log informations for possible future needs
    print('Logging webhook information')

    was_logged = log_webhook_info(options, id_webhook)

    if was_logged:
        print(
            'Success! The webhook for the %s stream from the %s Trello board was successfully created.' % (
                options.stream_name,
                options.trello_board_name
            )
        )

        print('\nYou can find the webhooks information in the zulip_trello_webhooks.csv file.')

    return True


def main() -> None:
    options = parser.parse_args()
    if check_configuration():
        creation_status = create_webhook(options)


if __name__ == '__main__':
    main()

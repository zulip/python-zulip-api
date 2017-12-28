from six.moves.configparser import SafeConfigParser
from typing import Dict, Any, Union
import requests
import logging
import sys
import os
import re

class IDoneThisHandler(object):
    '''
    This plugin posts entries from I Done This to Zulip.
    Data is provided by I Done This, through the public API.
    The bot looks for messages starting with @mention of the bot
    and responds with a message with a list of entries completed by the team.
    It also responds to private messages.
    '''
    def usage(self) -> str:
        return '''
            This plugin allows users to get a list of entries in I Done This.
            Users should preface keywords with the IDoneThis-bot @mention.
            The bot responds also to private messages.
            '''

    def initialize(self, bot_handler: Any) -> None:
        self.config_info = bot_handler.get_config_info('idonethis')

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        bot_response = get_bot_idonethis_response(
            message,
            bot_handler,
            self.config_info
        )
        bot_handler.send_reply(message, bot_response)


class IDoneThisNoResultException(Exception):
    pass


def get_entries_idonethis(number: int, team_id: str, api_key: str) -> Union[int, str]:
    # Return the last x number of entries from I Done This.
    # In case of error, e.g. failure to fetch entries, it will
    # return a number.
    url = ('https://beta.idonethis.com/api/v2/entries?team_id=%s' % (team_id))
    auth_token = ('Token %s' % (api_key))
    auth = {'Authorization': auth_token}
    try:
        data = requests.get(url, headers=auth)
    except requests.exceptions.ConnectionError as e:  # Usually triggered by bad connection.
        logging.exception('Bad connection')
        raise
    data.raise_for_status()
    try:
        counter = 0
        while (counter < number):
            entries += data.json()[counter]['body']
            counter = counter + 1
    except (TypeError, KeyError):  # Usually triggered by no result in IDoneThis.
        raise IDoneThisNoResultException()

    return entries


def get_bot_idonethis_response(message: Dict[str, str], bot_handler: Any, config_info: Dict[str, str]) -> str:
    # Each exception has a specific reply should "get_entries" return a number.
    # The bot will post the appropriate message for the error.
    keyword = message['content']
    try:
        entries = get_entries_idonethis(keyword, config_info['team'], config_info['key'])
    except requests.exceptions.ConnectionError:
        return ('Uh oh, sorry :slightly_frowning_face:, I '
                'cannot process your request right now. But, '
                'let\'s try again later! :grin:')
    except IDoneThisNoResultException:
        return ('Sorry, I don\'t have any I Done This Entries for your team.')
    return entries

handler_class = IDoneThisHandler

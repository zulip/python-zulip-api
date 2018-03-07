import logging
import requests
from typing import Any, Dict
from requests.exceptions import ConnectionError

USERS_LIST_URL = 'https://api.flock.co/v1/roster.listContacts'
SEND_MESSAGE_URL = 'https://api.flock.co/v1/chat.sendMessage'

help_message = '''
You can send messages to any Flock user associated with your account from Zulip.
*Syntax*: **@botname to: message** where `to` is **firstName** of recipient.
'''

# Matches the recipient name provided by user with list of users in his contacts.
# If matches, returns the matched User's ID
def find_recipient(res: str, to: str) -> str:
    for obj in res:
        if to == obj['firstName']:
            return obj['id']

# Returns User's ID, if not found, returns error message.
def get_recipient_id(content: str, config: Dict[str, str]) -> str:
    token = config['token']
    content_pieces = content.split(':')
    to = content_pieces[0].strip()
    payload = {
        'token': token
    }

    try:
        res = requests.get(USERS_LIST_URL, params=payload)
    except ConnectionError as e:
        logging.exception(str(e))
        return "Uh-Oh, couldn't process the request \
right now.\nPlease try again later"

    res = res.json()
    to = find_recipient(res, to)
    if to is None:
        return "No user found. Make sure you typed it correctly."
    else:
        return to

# This handles the message sending work.
def get_flock_response(content: str, config: Dict[str, str]) -> str:
    token = config['token']
    content_pieces = content.split(':')
    to = content_pieces[0].strip()
    message = content_pieces[1].strip()

    to = get_recipient_id(content, config)
    if len(str(to)) > 30:
        return to

    payload = {
        'to': to,
        'text': message,
        'token': token
    }
    try:
        r = requests.get(SEND_MESSAGE_URL, params=payload)
    except ConnectionError as e:
        logging.exception(str(e))
        return "Uh-Oh, couldn't process the request \
right now.\nPlease try again later"

    r = r.json()
    if "uid" in r:
        return "Message sent."
    else:
        return "Message sending failed :slightly_frowning_face:. Please try again."

def get_flock_bot_response(content: str, config: Dict[str, str]) -> None:
    content = content.strip()
    if content == '' or content == 'help':
        return help_message
    else:
        result = get_flock_response(content, config)
        return result

class FlockHandler(object):
    '''
    This is flock bot. Now you can send messages to any of your
    flock user without having to leave Zulip.
    '''

    def initialize(self, bot_handler: Any) -> None:
        self.config_info = bot_handler.get_config_info('flock')

    def usage(self) -> str:
        return '''Hello from Flock Bot. You can send messages to any Flock user
right from Zulip.'''

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        response = get_flock_bot_response(message['content'], self.config_info)
        bot_handler.send_reply(message, response)

handler_class = FlockHandler

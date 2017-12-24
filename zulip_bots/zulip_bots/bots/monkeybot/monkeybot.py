# See readme.md for instructions on running this code.

from typing import Any
import requests

class MonkeyBotHandler(object):
    def usage(self) -> str:
        return '''
        This is a boilerplate bot that responds to a user query with
        "beep boop", which is robot for "Hello World".

        This bot can be used as a template for other, more
        sophisticated, bots.
        '''

    def handle_message(self, message, bot_handler):
        original_content = message['content']
        original_sender = message['sender_email']
        if(original_content[:4] == "http"):
            request = requests.get(original_content)
            if request.status_code == 200:
                message['content'] = 'Site ' + original_content + ' exists'
            else:
                message['content'] = 'Site is not existing m8'
        else:
            message['content'] = 'Invalid syntax m8'

        bot_handler.send_message(dict(
            type='private',
            to=original_sender,
            content=message['content'],
))     
handler_class = MonkeyBotHandler

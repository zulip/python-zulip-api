# See readme.md for instructions on running this code.

from typing import Any

class GoogleHangoutsHandler(object):
    def usage(self) -> str:
        return '''
        This is a bot that posts a link to a Google Hangouts call.
        '''

    def handle_message(self, message: Any, bot_handler: Any) -> None:
        content = 'https://hangouts.google.com/'  # type: str
        bot_handler.send_reply(message, content)

handler_class = GoogleHangoutsHandler

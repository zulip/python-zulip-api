# See readme.md for instructions on running this code.

from typing import Dict, Any, Optional, Callable
import wit
import sys
import importlib.util

class WitaiHandler(object):
    def usage(self) -> str:
        return '''
        Wit.ai bot uses pywit API to interact with Wit.ai. In order to use
        Wit.ai bot, `witai.conf` must be set up. See `doc.md` for more details.
        '''

    def initialize(self, bot_handler: Any) -> None:
        config = bot_handler.get_config_info('witai')

        token = config.get('token')
        if not token:
            raise KeyError('No `token` was specified')

        # `handler_location` should be the location of a module which contains
        # the function `handle`. See `doc.md` for more details.
        handler_location = config.get('handler_location')
        if not handler_location:
            raise KeyError('No `handler_location` was specified')
        handle = get_handle(handler_location)
        if handle is None:
            raise Exception('Could not get handler from handler_location.')
        else:
            self.handle = handle

        help_message = config.get('help_message')
        if not help_message:
            raise KeyError('No `help_message` was specified')
        self.help_message = help_message

        self.client = wit.Wit(token)

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        if message['content'] == '' or message['content'] == 'help':
            bot_handler.send_reply(message, self.help_message)
            return

        try:
            res = self.client.message(message['content'])
            message_for_user = self.handle(res)

            if message_for_user:
                bot_handler.send_reply(message, message_for_user)
        except wit.wit.WitError:
            bot_handler.send_reply(message, 'Sorry, I don\'t know how to respond to that!')
        except Exception as e:
            bot_handler.send_reply(message, 'Sorry, there was an internal error.')
            print(e)
            return

handler_class = WitaiHandler

def get_handle(location: str) -> Optional[Callable[[Dict[str, Any]], Optional[str]]]:
    '''Returns a function to be used when generating a response from Wit.ai
    bot. This function is the function named `handle` in the module at the
    given `location`. For an example of a `handle` function, see `doc.md`.

    For example,

        handle = get_handle('/Users/someuser/witai_handler.py')  # Get the handler function.
        res = witai_client.message(message['content'])  # Get the Wit.ai response.
        message_res = self.handle(res)  # Handle the response and find what to show the user.
        bot_handler.send_reply(message, message_res)  # Send it to the user.

    Parameters:
     - location: The absolute path to the module to look for `handle` in.
    '''
    try:
        spec = importlib.util.spec_from_file_location('module.name', location)
        handler = importlib.util.module_from_spec(spec)
        loader = spec.loader
        if loader is None:
            return None
        loader.exec_module(handler)
        return handler.handle  # type: ignore
    except Exception as e:
        print(e)
        return None

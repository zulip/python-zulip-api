import os
from typing import Optional, Any, Dict

try:
    import aiml
except ImportError:
    raise ImportError("""It looks like you are missing aiml.
                      Please: pip3 install python-aiml""")

# See readme.md for instructions on running this code.

BOTS_DIR = os.path.dirname(os.path.abspath(__file__))
DIRECTORY_PATH = os.path.join(BOTS_DIR, 'assets')
AIML_PATH = os.path.join(BOTS_DIR, 'assets/std-startup.aiml')

def create_Bot():
    brain = aiml.Kernel()
    brain.bootstrap(learnFiles=AIML_PATH, commands="get brain")
    return brain

class AIBotHandler(object):
    '''
    This plugin facilitates running an AI Bot with custom aiml files.
    It looks for messages starting with '@mention-bot'

    In this example, we write all Ai Bot messages into
    the same stream that it was called from.
    '''

    META = {
        'name': 'ai_bot',
        'description': 'AI chat bot which can be customized as per user requirements.',
    }

    def usage(self) -> str:
        return '''
            This plugin will allow users to directly chat
            with custom made AI Bot.Users should preface
            query with "@mention-bot".
            @mention-bot <message>'''

    def initialize(self, bot_handler) -> None:
        self.bot_brain = create_Bot()

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        bot_response = self.get_ai_bot_response(message, bot_handler)
        bot_handler.send_reply(message, bot_response)

    def get_ai_bot_response(self, message: Dict[str, str], bot_handler: Any) -> Optional[str]:
        '''This function returns the URLs of the requested topic.'''

        help_text = 'Please enter your message after @mention-bot to chat with AI Bot'

        # Checking if the link exists.
        query = message['content']
        if query == '':
            return help_text

        new_content = '```AI Bot says: ```'
        response = self.bot_brain.respond(query)
        new_content += response
        return new_content

handler_class = AIBotHandler

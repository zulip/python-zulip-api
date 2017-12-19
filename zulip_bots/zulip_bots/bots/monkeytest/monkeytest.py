from typing import Any

import requests


class MonkeyTestHandler(object):
    def initialize(self, bot_handler: Any):
        self.config_info = bot_handler.get_config_info('monkeytest')

    def usage(self):
        return '''
        This is bot for Monkeytest.it(site for testing sites)
        '''

    def handle_message(self, message, bot_handler):
        content = message['content'].strip()
        if content == 'help' or content == '':
            bot_handler.send_reply(message,
                                   'This is bot for Monkeytest.it(site for testing sites)\nWrite me adress of site you want to test')
        else:
            if content.startswith('http://www.') or content.startswith('http://www.'):
                url = content
            else:
                if content.startswith('www.'):
                    url = 'http://' + content
                else:
                    url = 'http://www.' + content

            try:
                bot_handler.send_reply(message,"Wait please, I'm working")
                response = requests.get('https://monkeytest.it/test', params={
                    'url': url,
                    'secret': self.config_info['key'],
                })
                result = (response.json().get('results_url'))
                bot_handler.send_reply(message, ('Test for {}\n{}').format(url, result))
            except:
                bot_handler.send_reply(message, 'Something wrong')


handler_class = MonkeyTestHandler

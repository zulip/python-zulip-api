import configparser
import sys

class SimpleStorage:
    def __init__(self):
        self.data = dict()

    def contains(self, key):
        return (key in self.data)

    def put(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data[key]

class SimpleMessageServer:
    # This class is needed for the incrementor bot, which
    # actually updates messages!
    def __init__(self):
        self.message_id = 0
        self.messages = dict()

    def send(self, message):
        self.message_id += 1
        message['id'] = self.message_id
        self.messages[self.message_id] = message
        return message

    def update(self, message):
        self.messages[message['message_id']] = message

class TerminalBotHandler:
    def __init__(self, bot_config_file):
        self.bot_config_file = bot_config_file
        self.storage = SimpleStorage()
        self.message_server = SimpleMessageServer()

    def send_message(self, message):
        if message['type'] == 'stream':
            print('''
                stream: {} topic: {}
                {}
                '''.format(message['to'], message['subject'], message['content']))
        else:
            print('''
                PM response:
                {}
                '''.format(message['content']))
        return self.message_server.send(message)

    def send_reply(self, message, response):
        print("\nReply from the bot is printed between the dotted lines:\n-------\n{}\n-------".format(response))
        response_message = dict(
            content=response
        )
        return self.message_server.send(response_message)

    def update_message(self, message):
        self.message_server.update(message)
        print('''
            update to message #{}:
            {}
            '''.format(message['message_id'], message['content']))

    def get_config_info(self, bot_name, optional=False):
        if self.bot_config_file is None:
            if optional:
                return dict()
            else:
                print('Please supply --bot-config-file argument.')
                sys.exit(1)

        config = configparser.ConfigParser()
        with open(self.bot_config_file) as conf:
            config.readfp(conf)  # type: ignore # readfp->read_file in python 3, so not in stubs

        return dict(config.items(bot_name))

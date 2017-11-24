# See readme.md for instructions on running this code.


class IncrementorHandler(object):
    META = {
        'name': 'Incrementor',
        'description': 'Example bot to test the update_message() function.',
    }

    def usage(self):
        return '''
        This is a boilerplate bot that makes use of the
        update_message function. For the first @-mention, it initially
        replies with one message containing a `1`. Every time the bot
        is @-mentioned, this number will be incremented in the same message.
        '''

    def initialize(self, bot_handler):
        storage = bot_handler.storage
        if not storage.contains('number') or not storage.contains('message_id'):
            storage.put('number', 0)
            storage.put('message_id', None)

    def handle_message(self, message, bot_handler):
        storage = bot_handler.storage
        num = storage.get('number')
        storage.put('number', num + 1)
        if storage.get('message_id') is None:
            result = bot_handler.send_reply(message, str(storage.get('number')))
            storage.put('message_id', result['id'])
        else:
            bot_handler.update_message(dict(
                message_id = storage.get('message_id'),
                content = str(storage.get('number'))
            ))


handler_class = IncrementorHandler

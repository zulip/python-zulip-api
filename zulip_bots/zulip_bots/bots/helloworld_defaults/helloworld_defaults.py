# See readme.md for instructions on running this code.

class HelloWorld_DefaultBot(object):
    META = {
        'name': 'HelloWorld-defaults',
        'description': 'Minimal bot using default commands.',
    }
    def usage(self):
        return '''
        This is a simple bot that responds to *most* user queries with
        "beep boop", which is robot for "Hello World"; others are
        dealt with by the default-command system.

        This bot can be used as a template for other, more
        sophisticated, bots using default commands.
        '''

    def handle_message(self, message, bot_handler):
        default_commands_to_handle = ["", "about"]
        default_response = bot_handler.dispatch_default_commands(message,
                                                                 default_commands_to_handle,
                                                                 self.META)
        if default_response is not None:
            bot_handler.send_reply(message, default_response)
            return

        content = 'beep boop'
        bot_handler.send_reply(message, content)

handler_class = HelloWorld_DefaultBot

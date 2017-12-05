# See readme.md for instructions on running this code.

import six.moves.configparser
class FollowupHandler(object):
    '''
    This plugin facilitates creating follow-up tasks when
    you are using Zulip to conduct a virtual meeting.  It
    looks for messages starting with '@mention-bot'.

    In this example, we write follow up items to a special
    Zulip stream called "followup," but this code could
    be adapted to write follow up items to some kind of
    external issue tracker as well.
    '''

    def usage(self):
        return '''
            This plugin will allow users to flag messages
            as being follow-up items.  Users should preface
            messages with "@mention-bot".

            Before running this, make sure to create a stream
            called "followup" that your API user can send to.
            '''

    def initialize(self, bot_handler):
            self.config_info = bot_handler.get_config_info('stream_detail', optional=True)
            self.default_stream = self.config_info.get("stream", False)
            self.default_stream = 'followup'

    def handle_message(self, message, bot_handler):
        if message['content'] == '':
            bot_response = "Please specify the message you want to send to followup stream after @mention-bot"
            bot_handler.send_reply(message, bot_response)
        else:
            bot_response = self.get_bot_followup_response(message)
            default_stream = self.default_stream
            bot_handler.send_message(dict(
                type='stream',
                to=default_stream,
                subject=message['sender_email'],
                content=bot_response,
            ))

    def get_bot_followup_response(self, message):
        original_content = message['content']
        original_sender = message['sender_email']
        temp_content = 'from %s: ' % (original_sender,)
        new_content = temp_content + original_content

        return new_content

handler_class = FollowupHandler

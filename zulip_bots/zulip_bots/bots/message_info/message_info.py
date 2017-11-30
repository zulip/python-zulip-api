# See readme.md for instructions on running this code.


class MessageInfoHandler(object):
    def usage(self):
        return '''This bot will allow users to analyze a message for letter
            count and word count. The gathered information will then be sent to
            a private conversation with the user. Users should @-mention the
            bot in the beginning of a message.
            '''

    def handle_message(self, message, bot_handler):
        words_in_message = message['content'].split()

        unformatted_content = 'You sent a message with {} words.'
        content = unformatted_content.format(len(words_in_message))

        original_sender = message['sender_email']
        bot_handler.send_message({
            'type': 'private',
            'to': original_sender,
            'content': content,
        })

handler_class = MessageInfoHandler

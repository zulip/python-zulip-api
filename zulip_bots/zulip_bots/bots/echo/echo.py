from typing import Any, Dict

class EchoHandler(object):
    def usage(self) -> str:
        return '''
            This plugin will echo messages or zgrams back
            to the sender.  This bot is mostly useful for
            debugging bot infrastructure or doing sanity
            checks for dev installs.
            '''

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        echo_content = 'echo: ' + message['content']
        bot_handler.send_reply(message, echo_content)

    def handle_zgram(self, data: Dict[str, Any], bot_handler: Any) -> None:
        reply_content = 'echo: ' + data['content']
        reply_data = dict(
            target_user_id=data['sender_id'],
            content=reply_content
        )
        bot_handler.send_zgram(reply_data)

handler_class = EchoHandler

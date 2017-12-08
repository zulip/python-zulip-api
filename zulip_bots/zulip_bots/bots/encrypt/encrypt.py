from typing import Any, Dict

def encrypt(text: str) -> str:
    # This is where the actual ROT13 is applied
    # WHY IS .JOIN NOT WORKING?!
    textlist = list(text)
    newtext = ''
    firsthalf = 'abcdefghijklmABCDEFGHIJKLM'
    lasthalf = 'nopqrstuvwxyzNOPQRSTUVWXYZ'
    for char in textlist:
        if char in firsthalf:
            newtext += lasthalf[firsthalf.index(char)]
        elif char in lasthalf:
            newtext += firsthalf[lasthalf.index(char)]
        else:
            newtext += char

    return newtext

class EncryptHandler(object):
    '''
    This bot allows users to quickly encrypt messages using ROT13 encryption.
    It encrypts/decrypts messages starting with @mention-bot.
    '''

    def usage(self) -> str:
        return '''
            This bot uses ROT13 encryption for its purposes.
            It responds to me starting with @mention-bot.
            Feeding encrypted messages into the bot decrypts them.
            '''

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        bot_response = self.get_bot_encrypt_response(message)
        bot_handler.send_reply(message, bot_response)

    def get_bot_encrypt_response(self, message: Dict[str, str]) -> str:
        original_content = message['content']
        temp_content = encrypt(original_content)
        send_content = "Encrypted/Decrypted text: " + temp_content
        return send_content

handler_class = EncryptHandler

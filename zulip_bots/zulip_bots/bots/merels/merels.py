from zulip_bots.bots.merels.libraries import game


class MerelsBot(object):
    """
    Simulate the merels game to the chat
    """

    def __init__(self):
        pass

    def usage(self):
        return game.getInfo()

    def handle_message(self, message, bot_handler):
        room_name = self.compose_room_name(message)
        content = message['content']

        response = game.beat(content, room_name, bot_handler.storage)

        bot_handler.send_reply(message, response)

    def compose_room_name(self, message):
        room_name = "test"
        if "type" in message:
            if message['type'] == "stream":
                if 'subject' in message:
                    realm = message['sender_realm_str']
                    stream = message['display_recipient']
                    topic = message['subject']
                    room_name = "{}-{}-{}".format(realm, stream, topic)
            else:
                # type == "private"
                realm = message['sender_realm_str']
                users_list = [recipient['email'] for recipient in message[
                    'display_recipient']]
                users = "-".join(sorted(users_list))
                room_name = "{}-{}".format(realm, users)
        return room_name


handler_class = MerelsBot

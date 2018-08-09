import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr, Event, ServerConnection
from typing import Any, Dict

IRC_DOMAIN = "irc.example.com"

def zulip_sender(sender_string):
    # type: (str) -> str
    nick = sender_string.split("!")[0]
    return nick + "@" + IRC_DOMAIN

class IRCBot(irc.bot.SingleServerIRCBot):
    def __init__(self, zulip_client, channel, nickname, server, port=6667):
        # type: (Any, irc.bot.Channel, str, str, int) -> None
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel  # type: irc.bot.Channel
        self.zulip_client = zulip_client

    def on_nicknameinuse(self, c, e):
        # type: (ServerConnection, Event) -> None
        c.nick(c.get_nickname().replace("_zulip", "__zulip"))

    def on_welcome(self, c, e):
        # type: (ServerConnection, Event) -> None
        c.join(self.channel)

        def forward_to_irc(msg):
            # type: (Dict[str, Any]) -> None
            if msg["type"] == "stream":
                send = lambda x: c.privmsg(msg["display_recipient"], x)
            else:
                recipients = [u["short_name"] for u in msg["display_recipient"] if
                              u["email"] != msg["sender_email"]]
                if len(recipients) == 1:
                    send = lambda x: c.privmsg(recipients[0], x)
                else:
                    send = lambda x: c.privmsg_many(recipients, x)
            for line in msg["content"].split("\n"):
                send(line)

        ## Forwarding from Zulip => IRC is disabled; uncomment the next
        ## line to make this bot forward in that direction instead.
        #
        # self.zulip_client.call_on_each_message(forward_to_irc)

    def on_privmsg(self, c, e):
        # type: (ServerConnection, Event) -> None
        content = e.arguments[0]
        sender = zulip_sender(e.source)
        if sender.endswith("_zulip@" + IRC_DOMAIN):
            return

        # Forward the PM to Zulip
        print(self.zulip_client.send_message({
            "sender": sender,
            "type": "private",
            "to": "username@example.com",
            "content": content,
        }))

    def on_pubmsg(self, c, e):
        # type: (ServerConnection, Event) -> None
        content = e.arguments[0]
        stream = e.target
        sender = zulip_sender(e.source)
        if sender.endswith("_zulip@" + IRC_DOMAIN):
            return

        # Forward the stream message to Zulip
        print(self.zulip_client.send_message({
            "forged": "yes",
            "sender": sender,
            "type": "stream",
            "to": stream,
            "subject": "IRC",
            "content": content,
        }))

    def on_dccmsg(self, c, e):
        # type: (ServerConnection, Event) -> None
        c.privmsg("You said: " + e.arguments[0])

    def on_dccchat(self, c, e):
        # type: (ServerConnection, Event) -> None
        if len(e.arguments) != 2:
            return
        args = e.arguments[1].split()
        if len(args) == 4:
            try:
                address = ip_numstr_to_quad(args[2])
                port = int(args[3])
            except ValueError:
                return
            self.dcc_connect(address, port)

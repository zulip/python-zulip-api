import logging
import multiprocessing as mp
import sys
from typing import Any, Dict, Optional

import irc.bot
import irc.strings
from irc.client import Event, ServerConnection, ip_numstr_to_quad


class IRCBot(irc.bot.SingleServerIRCBot):
    def __init__(
        self,
        zulip_client: Any,
        stream: str,
        topic: str,
        channel: irc.bot.Channel,
        nickname: str,
        server: str,
        nickserv_password: str = "",
        port: int = 6667,
        sasl_password: Optional[str] = None,
    ) -> None:
        self.channel: irc.bot.Channel = channel
        self.zulip_client = zulip_client
        self.stream = stream
        self.topic = topic
        self.IRC_DOMAIN = server
        self.nickserv_password = nickserv_password
        # Make sure the bot is subscribed to the stream
        self.check_subscription_or_die()
        # Initialize IRC bot after proper connection to Zulip server has been confirmed.
        if sasl_password is not None:
            irc.bot.SingleServerIRCBot.__init__(
                self, [(server, port, sasl_password)], nickname, nickname, sasl_login=nickname
            )
        else:
            irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)

    def zulip_sender(self, sender_string: str) -> str:
        nick = sender_string.split("!")[0]
        return nick + "@" + self.IRC_DOMAIN

    def check_subscription_or_die(self) -> None:
        resp = self.zulip_client.get_subscriptions()
        if resp["result"] != "success":
            print("ERROR: {}".format(resp["msg"]))
            sys.exit(1)
        subs = [s["name"] for s in resp["subscriptions"]]
        if self.stream not in subs:
            print(
                f"The bot is not yet subscribed to stream '{self.stream}'. Please subscribe the bot to the stream first."
            )
            sys.exit(1)

    def on_nicknameinuse(self, c: ServerConnection, e: Event) -> None:
        c.nick(c.get_nickname().replace("_zulip", "__zulip"))

    def on_welcome(self, c: ServerConnection, e: Event) -> None:
        if len(self.nickserv_password) > 0:
            msg = f"identify {self.nickserv_password}"
            c.privmsg("NickServ", msg)
        c.join(self.channel)

        def forward_to_irc(msg: Dict[str, Any]) -> None:
            not_from_zulip_bot = msg["sender_email"] != self.zulip_client.email
            if not not_from_zulip_bot:
                # Do not forward echo
                return
            is_a_stream = msg["type"] == "stream"
            if is_a_stream:
                in_the_specified_stream = msg["display_recipient"] == self.stream
                at_the_specified_subject = msg["subject"].casefold() == self.topic.casefold()
                if in_the_specified_stream and at_the_specified_subject:
                    msg["content"] = "@**{}**: ".format(msg["sender_full_name"]) + msg["content"]
                    send = lambda x: c.privmsg(self.channel, x)
                else:
                    return
            else:
                recipients = [
                    u["short_name"]
                    for u in msg["display_recipient"]
                    if u["email"] != msg["sender_email"]
                ]
                if len(recipients) == 1:
                    send = lambda x: c.privmsg(recipients[0], x)
                else:
                    send = lambda x: c.privmsg_many(recipients, x)
            for line in msg["content"].split("\n"):
                send(line)

        z2i = mp.Process(target=self.zulip_client.call_on_each_message, args=(forward_to_irc,))
        z2i.start()

    def on_privmsg(self, c: ServerConnection, e: Event) -> None:
        content = e.arguments[0]
        sender = self.zulip_sender(e.source)
        if sender.endswith("_zulip@" + self.IRC_DOMAIN):
            return

        # Forward the PM to Zulip
        print(
            self.zulip_client.send_message(
                {
                    "sender": sender,
                    "type": "private",
                    "to": "username@example.com",
                    "content": content,
                }
            )
        )

    def on_pubmsg(self, c: ServerConnection, e: Event) -> None:
        content = e.arguments[0]
        sender = self.zulip_sender(e.source)
        if sender.endswith("_zulip@" + self.IRC_DOMAIN):
            return

        # Forward the stream message to Zulip
        print(
            self.zulip_client.send_message(
                {
                    "type": "stream",
                    "to": self.stream,
                    "subject": self.topic,
                    "content": f"**{sender}**: {content}",
                }
            )
        )

    def on_dccmsg(self, c: ServerConnection, e: Event) -> None:
        c.privmsg("You said: " + e.arguments[0])

    def on_dccchat(self, c: ServerConnection, e: Event) -> None:
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

    def on_error(self, c: ServerConnection, e: Event) -> None:
        logging.error("error from server: %s", e.target)

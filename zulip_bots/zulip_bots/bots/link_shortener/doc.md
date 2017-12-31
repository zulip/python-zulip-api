# Link Shortener Bot

Link Shortener Bot is a Zulip bot that will shorten URLs ("links") in a
conversation. It uses the [goo.gl URL shortener API] to shorten its links.

Use [this](https://developers.google.com/url-shortener/v1/getting_started) to get
your API Key.

Links can be anywhere in the message, for example,

 > @**Link Shortener Bot** @**Joe Smith** See
 > https://github.com/zulip/python-zulip-api/tree/master/zulip_bots/zulip_bots/bots
 > for a list of all Zulip bots.

and LS Bot would respond

 > https://github.com/zulip/python-zulip-api/tree/master/zulip_bots/zulip_bots/bots:
 > **https://goo.gl/NjLZZH**

[goo.gl URL shortener API]: https://goo.gl

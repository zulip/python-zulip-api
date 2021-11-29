# Discord<->Zulip bridge

It supports basic text mirroring between Discord guilds and Zulip
streams (within a single Zulip realm). On both the Discord and Zulip
sides, it can either send as a single bot with limited special
permissions, or with special permissions (webhooks and can_forge_sender
respectively), it can more naturally mirror them.

This design more naturally fits a personal Zulip realm supporting many Discord
guilds than a single organization that wants to run on both Zulip and Discord.
For that, you might want each Discord channel to match a Zulip stream, and
Discord threads to match Zulip topics. Supporting this mode of operation as
well would be a good future enhancement.

There is currently no special support for threads, media, embeds,
reactions, etc..

Configuration lives in a single `bridge.ini` file. A template can be created by running:
```
bridge.py --write-sample-config=bridge.ini --from-zuliprc=zuliprc
```

(The `zuliprc` is optional; see the Zulip section for details on getting it.)

Configuration consists of a `discord` section, `zulip` section, and a list of guilds and streams to associate.

With the exception of the stream<->guild setup, all configuration is global. Some features that might make sense to make configurable by guild:
- Whether to use webhooks to forge Discord senders
- How to create a topic name from a Discord thread

## Discord

Create a Discord integration (https://discord.com/developers/applications/)

Grant it the following permissions:
- Manage webhooks (to set the sender name)
- Read messages / view channels
- Send messages
- Create public threads
- Create private threads
- Send messages in threads
- Read message history

This will produce a URL with these permissions and some client ID, along the lines of:
https://discord.com/api/oauth2/authorize?client_id=914346072418185256&permissions=378494061568&scope=bot

Following this link will allow adding the integration to a Discord server you have Manager Server permissions on.


On the "Bot" tab, add a bot. Copy the token into the `token` key of the
`discord` section of the config file. Enable "message content intent" -- this
is a privileged intent, so if you want to use the bot with more than 100
guilds, you'll need to get your bot reviewed. For typical uses with only a
handful of guilds, though, no review is needed.

The manage webhooks permission is optional, but makes messages forwarded to
Discord look more native; if you wish to disable it, set the `use_webhook` key
in the `discord` section to false.

## Zulip

For Zulip setup, create a bot user (gear -> personal settings -> Bots -> Add a
new bot) and download a `zuliprc`. Then, you can run `bridge.py
--write-sample-config --from-zuliprc=zuliprc` to create a sample config based
on that `zuliprc`.

Forging senders is optional -- it will make messages forwarded to Zulip look
more natural, but requires special permissions. To use it:
- Set the `forge_sender` key of the `zulip` section to `true` in your
  `bridge.ini` file, and run `./manage.py change_user_role -r discord-mirror
  discord-bot@discord-mirror.zulip.org can_forge_sender` (adjust realm and bot
  name appropriately) on your Zulip server to grant permissions.
- Add a `RealmDomain` of "users.discord.com": under gear -> Manage organization
  -> Organization permissions -> Restrict email domains of new users?, choose
  to restrict to a list of domains, and add "users.discord.com". You can then
  freely switch back to "Don't allow disposable email addresses" or another
  value for that setting, if you wish.
- Note that for technical reasons, forging senders involves pretending to be a
  Jabber mirror; as a result, sender names will include " (XMPP)" after them.
  (If you prefer to show " (irc)", you can change `jabber_mirror` to
  `irc_mirror` in `bridge.py`. It should also be a simple server patch to
  support another client name with no suffix or a different suffix.)

## Streams

The `streams` section has no specific keys. Instead, each key is a stream name,
and the corresponding value is a Discord guild ID. To find a guild ID, open the
the Discord webapp, and navigate to the guild (server). You should see a URL
like `https://discord.com/channels/<guild>/<channel>`, where `<guild>` is the
guild ID to use.

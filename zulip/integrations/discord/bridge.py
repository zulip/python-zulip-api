#!/usr/bin/env python

"""Discord/Zulip bridge"""

import argparse
import asyncio
import configparser
import logging
import os
import re
import sys
import traceback
from typing import Any, Dict, Optional, Tuple, Union, cast

import discord

import zulip
import zulip.asynch

LOG_FORMAT = "%(asctime)s %(levelname)7s - %(name)20s - %(message)s"
logger = logging.getLogger(__name__)


class Bridge_ConfigException(Exception):
    pass


class Bridge_ZulipFatalException(Exception):
    pass


# Zulip uses Django to validate emails, which provides an EmailValidator class
# https://github.com/django/django/blob/main/django/core/validators.py#L158
# This regex is copied from there
EMAIL_USER_RE = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\Z"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)',  # quoted-string
    re.IGNORECASE,
)


class GuildConfig:
    def __init__(self, stream: str) -> None:
        self.stream = stream
        self.webhooks: Dict[int, discord.Webhook] = {}


class Bridge:
    "Zulip/Discord bridge" ""

    def __init__(
        self,
        discord_config: Dict[str, Union[str, bool]],
        zulip_client: zulip.asynch.AsyncClient,
        zulip_config: Dict[str, Union[str, bool]],
        streams: Dict[str, int],
    ) -> None:
        self._discord_config = discord_config
        # The Discord client doesn't have any useful configuration (the token
        # is supplied to the login() method), but does embed the event loop
        # The intent is that Bridge can be created before starting the event
        # loop, so while the Zulip client (which includes config) is passed in,
        # the Discord client is created when needed.
        self._discord_client: Optional[discord.Client] = None
        self._zulip_client = zulip_client
        self._streams = streams
        self._guilds = self._build_guild_config(streams)
        self._discord_domain = zulip_config.get("discord_domain", "users.discord.com")
        self._default_stream = zulip_config.get("default_stream")
        self._default_topic = zulip_config.get("default_topic", "(no topic)")
        self._forge_zulip = zulip_config["forge_sender"]

    @staticmethod
    def _build_guild_config(streams: Dict[str, int]) -> Dict[int, GuildConfig]:
        ret = {}
        for stream, guild_id in streams.items():
            ret[guild_id] = GuildConfig(stream)
        return ret

    def get_zulip_stream_and_topic_from_discord(self, message: discord.Message) -> Tuple[str, str]:
        stream = self._guilds[message.guild.id].stream
        topic = message.channel.name
        return stream, topic

    def get_zulip_sender_from_discord(self, sender: discord.abc.User) -> str:
        if EMAIL_USER_RE.match(sender.display_name):
            user_part = sender.display_name
        else:
            logger.debug(
                "Sender %s display_name='%s' invalid user part, using name='%s'",
                sender,
                sender.display_name,
                sender.name,
            )
            user_part = sender.name
        return user_part + "@" + self._discord_domain

    async def on_discord_message(self, message: discord.Message) -> None:
        logger.info(f'Discord message from {message.author}: "{message.content}" {message}')

        # Avoid mirroring our own messages
        assert self._discord_client
        if message.author == self._discord_client.user:
            logger.info("Ignoring message from self: %s", message)
            return
        if message.webhook_id:
            guild_config = self._guilds[message.guild.id]
            webhook = guild_config.webhooks.get(message.channel.id)
            if webhook and webhook.id == message.webhook_id:
                # There is a small race here: if we restarted after sending a
                # zulip->Discord message, we might process it post-restart
                # before adding the webhook to the webhook cache. That's
                # probably an acceptable risk
                logger.info("Message sent through our webhook, ignoring: %s", message)
                return

        # Send it to Zulip
        stream, topic = self.get_zulip_stream_and_topic_from_discord(message)
        if self._forge_zulip:
            content = message.content  # TODO: consider including embeds, etc.
            out_msg = dict(
                forged="yes",
                sender=self.get_zulip_sender_from_discord(message.author),
                type="stream",
                subject=topic,
                to=stream,
                content=content,
            )
        else:
            content = "***%s***: %s" % (message.author, message.content)
            out_msg = dict(
                type="stream",
                subject=topic,
                to=stream,
                content=content,
            )
        logger.info("About to send: %s", out_msg)
        response = await self._zulip_client.send_message(out_msg)
        logger.info("Zulip send message response: %s", response)

    def get_channel_from_zulip(self, message: Dict[str, Any]) -> Optional[discord.TextChannel]:
        stream = message["display_recipient"]
        topic = message["subject"]
        try:
            guild_id = self._streams[stream]
        except KeyError:
            logger.warning("Couldn't find guild for stream %s: message %s", stream, message)
            return None
        assert self._discord_client
        guild = self._discord_client.get_guild(guild_id)
        if not guild:
            logger.warning(
                "Guild ID %s not found, for stream %s: message %s, guilds=%s",
                guild_id,
                stream,
                message,
                self._discord_client.guilds,
            )
            return None
        channel = discord.utils.get(guild.channels, name=topic)
        if not channel:
            logger.warning("Channel %s not found in guild %s: message %s", topic, guild, message)
            return None
        return channel

    async def get_webhook_for_discord_channel(
        self, channel: discord.TextChannel
    ) -> Optional[discord.Webhook]:
        if not self._discord_config["use_webhook"]:
            # Discord webhooks are disabled
            return None

        # Relevant docs:
        # https://docs.pycord.dev/en/master/api.html#discord.TextChannel.create_webhook
        # https://docs.pycord.dev/en/master/api.html#discord.TextChannel.webhooks
        # https://discordpy.readthedocs.io/en/latest/api.html#discord.utils.get

        guild_config = self._guilds[channel.guild.id]

        # Check the cache
        webhook = guild_config.webhooks.get(channel.id)
        if webhook:
            return webhook

        # See if we created one previously
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name="zulip_mirror")
        logger.info("Checked channel %s for existing webhooks, got %s", channel, webhook)
        if not webhook:
            # Create a new one
            reason = "custom sender for zulip mirror"
            webhook = await channel.create_webhook(name="zulip_mirror", reason=reason)
        # Cache and return
        guild_config.webhooks[channel.id] = webhook
        return webhook

    async def on_zulip_message(self, message: Dict[str, Any]) -> None:
        logger.info("Zulip message: %s", message)
        if message["type"] != "stream":
            # ignore personals
            return
        sender = message["sender_full_name"]

        # Check if this was a message we might have sent
        # Note that there is some server side filtering for clients named
        # "mirror", but that might change, so do it ourselves too. See also
        # https://chat.zulip.org/#narrow/stream/127-integrations/topic/suppressed.20own.20messages/near/1287622
        if message["client"] == self._zulip_client.sync_client.client_name:
            logger.info("Ignoring message %s from mirroring client %s", message, message["client"])
            return

        # Send to Discord
        channel = self.get_channel_from_zulip(message)
        if not channel:
            # get_channel_from_zulip will have logged a warning
            return
        # TODO: consider including embeds, etc.
        webhook = await self.get_webhook_for_discord_channel(channel)
        if webhook:
            await webhook.send(username=sender, content=message["content"])
            return
        content = "%s: %s" % (sender, message["content"])
        await channel.send(content=content)

    async def run_tasks(self) -> None:
        logger.info("Starting tasks...")
        logger.info("Connecting to discord...")
        assert not self._discord_client
        intents = discord.Intents(messages=True, guilds=True)
        self._discord_client = discord.Client(intents=intents)
        await self._discord_client.login(self._discord_config["token"])

        print("Creating message handler on Zulip client")
        zulip_await = self._zulip_client.call_on_each_message(self.on_zulip_message)

        print("Creating message handler on Discord client")

        @self._discord_client.event
        async def on_message(message: discord.Message) -> None:
            """Discord message-handling callback"""
            await self.on_discord_message(message)

        discord_await = self._discord_client.connect()

        awaitables = [zulip_await, discord_await]
        logger.info("awaitables=%s", awaitables)
        await asyncio.gather(*awaitables)
        logger.info("run_tasks finished...")


def generate_parser() -> argparse.ArgumentParser:
    description = """
    Script to bridge between Zulip and Discord.
    """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-c", "--config", required=False, help="Path to the config file for the bridge."
    )
    parser.add_argument(
        "--write-sample-config",
        metavar="PATH",
        dest="sample_config",
        help="Generate a configuration template at the specified location.",
    )
    parser.add_argument(
        "--from-zuliprc",
        metavar="ZULIPRC",
        dest="zuliprc",
        help="Optional path to zuliprc file for bot, when using --write-sample-config",
    )
    return parser


def read_configuration(config_file: str) -> Dict[str, Dict[str, Union[str, bool]]]:
    config = configparser.ConfigParser()

    try:
        config.read(config_file)
    except configparser.Error as exception:
        raise Bridge_ConfigException(str(exception))

    if set(config.sections()) != {"discord", "zulip", "streams"}:
        raise Bridge_ConfigException(
            "Please ensure the configuration has discord, zulip, and streams sections."
        )

    # TODO Could add more checks for configuration content here

    parsed: Dict[str, Dict[str, Union[str, bool]]] = {
        section: dict(config[section]) for section in config.sections()
    }
    parsed["zulip"]["forge_sender"] = config.getboolean("zulip", "forge_sender", fallback=False)
    parsed["discord"]["use_webhook"] = config.getboolean("discord", "use_webhook", fallback=True)
    return parsed


def write_sample_config(target_path: str, zuliprc: Optional[str]) -> None:
    if os.path.exists(target_path):
        raise Bridge_ConfigException(
            "Path '{}' exists; not overwriting existing file.".format(target_path)
        )

    sample_dict = dict(
        zulip=dict(
            email="discord-bot@chat.zulip.org",
            api_key="aPiKeY",
            site="https://chat.zulip.org",
            forge_sender="false",
        ),
        discord=dict(
            token="bot_token",
            use_webhook="true",
        ),
        streams={
            "test here": "guild ID",
        },
    )

    if zuliprc is not None:
        if not os.path.exists(zuliprc):
            raise Bridge_ConfigException("Zuliprc file '{}' does not exist.".format(zuliprc))

        zuliprc_config = configparser.ConfigParser()
        try:
            zuliprc_config.read(zuliprc)
        except configparser.Error as exception:
            raise Bridge_ConfigException(str(exception))

        # Can add more checks for validity of zuliprc file here

        sample_dict["zulip"]["email"] = zuliprc_config["api"]["email"]
        sample_dict["zulip"]["site"] = zuliprc_config["api"]["site"]
        sample_dict["zulip"]["api_key"] = zuliprc_config["api"]["key"]

    sample = configparser.ConfigParser()
    sample.read_dict(sample_dict)
    with open(target_path, "w") as target:
        sample.write(target)


def main() -> None:
    # signal.signal(signal.SIGINT, die)
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    parser = generate_parser()
    options = parser.parse_args()

    if options.sample_config:
        try:
            write_sample_config(options.sample_config, options.zuliprc)
        except Bridge_ConfigException as exception:
            print("Could not write sample config: {}".format(exception))
            sys.exit(1)
        if options.zuliprc is None:
            print("Wrote sample configuration to '{}'".format(options.sample_config))
        else:
            print(
                "Wrote sample configuration to '{}' using zuliprc file '{}'".format(
                    options.sample_config, options.zuliprc
                )
            )
        sys.exit(0)
    elif not options.config:
        print("Options required: -c or --config to run, OR --write-sample-config.")
        parser.print_usage()
        sys.exit(1)

    try:
        config = read_configuration(options.config)
    except Bridge_ConfigException as exception:
        print("Could not parse config file: {}".format(exception))
        sys.exit(1)

    # Get config for each client
    discord_config = config["discord"]
    zulip_config = config["zulip"]
    stream_config = {stream: int(guild) for stream, guild in config["streams"].items()}
    logger.info("zulip_config=%s", zulip_config)

    # Initiate clients
    backoff = zulip.asynch.RandomExponentialBackoff(timeout_success_equivalent=300)
    while backoff.keep_going():
        print("Starting mirroring bot")
        try:
            if zulip_config.get("forge_sender"):
                # An odd "security"(?) measure is that only certain clients
                # names can forge messages, even if they have the "super-admin"
                # permission
                client = "jabber_mirror"
            else:
                client = "discord_mirror"
            zulip_sync_client = zulip.Client(
                email=cast(str, zulip_config["email"]),
                api_key=cast(str, zulip_config["api_key"]),
                site=cast(str, zulip_config["site"]),
                client=client,
                verbose=True,
            )

            zulip_async_client = zulip.asynch.AsyncClient(zulip_sync_client)

            bridge = Bridge(discord_config, zulip_async_client, zulip_config, stream_config)

            logger.info("About to run_tasks")
            asyncio.run(bridge.run_tasks())
            logger.info("Finished run()")

            break

        except Bridge_ZulipFatalException as exception:
            sys.exit("Zulip bridge error: {}".format(exception))
        except zulip.ZulipError as exception:
            sys.exit("Zulip error: {}".format(exception))
        except Exception:
            traceback.print_exc()
        backoff.fail()


if __name__ == "__main__":
    main()

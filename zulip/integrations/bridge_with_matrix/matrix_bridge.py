#!/usr/bin/env python3
import argparse
import asyncio
import configparser
import logging
import os
import re
import signal
import sys
import traceback
import urllib.request
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from typing import Any, ClassVar, Dict, List, Match, Optional, Set, Tuple, Type, Union

import nio
from nio.responses import (
    DownloadError,
    DownloadResponse,
    ErrorResponse,
    JoinError,
    JoinResponse,
    LoginError,
    LoginResponse,
    Response,
    SyncError,
    SyncResponse,
)

import zulip

# change these templates to change the format of displayed message
ZULIP_MESSAGE_TEMPLATE: str = "**{username}** [{uid}]: {message}"
MATRIX_MESSAGE_TEMPLATE: str = "<{username} ({uid})> {message}"


class BridgeConfigError(Exception):
    pass


class BridgeFatalMatrixError(Exception):
    pass


class BridgeFatalZulipError(Exception):
    pass


class MatrixToZulip:
    """
    Matrix -> Zulip
    """

    non_formatted_messages: ClassVar[Dict[Type[nio.Event], str]] = {
        nio.StickerEvent: "sticker",
    }

    def __init__(
        self,
        matrix_client: nio.AsyncClient,
        matrix_config: Dict[str, Any],
        zulip_client: zulip.Client,
        no_noise: bool,
    ) -> None:
        self.matrix_client: nio.AsyncClient = matrix_client
        self.matrix_config: Dict[str, Any] = matrix_config
        self.zulip_client: zulip.Client = zulip_client
        self.no_noise: bool = no_noise

    @classmethod
    async def create(
        cls,
        matrix_client: nio.AsyncClient,
        matrix_config: Dict[str, Any],
        zulip_client: zulip.Client,
        no_noise: bool,
    ) -> "MatrixToZulip":
        matrix_to_zulip: "MatrixToZulip" = cls(matrix_client, matrix_config, zulip_client, no_noise)

        # Login to Matrix
        await matrix_to_zulip.matrix_login()
        await matrix_to_zulip.matrix_join_rooms()

        # Do an initial sync of the matrix client in order to continue with
        # the new messages and not with all the old ones.
        sync_response: Union[SyncResponse, SyncError] = await matrix_client.sync()
        if isinstance(sync_response, nio.SyncError):
            raise BridgeFatalMatrixError(sync_response.message)

        return matrix_to_zulip

    async def _matrix_to_zulip(self, room: nio.MatrixRoom, event: nio.Event) -> None:
        logging.debug("_matrix_to_zulip; room %s, event: %s", room.room_id, event)

        # We do this to identify the messages generated from Zulip -> Matrix
        # and we make sure we don't forward it again to the Zulip stream.
        if event.sender == self.matrix_config["mxid"]:
            return

        if room.room_id not in self.matrix_config["bridges"]:
            return
        stream, topic = self.matrix_config["bridges"][room.room_id]

        content: Optional[str] = await self.get_message_content_from_event(event, room)
        if not content:
            return

        try:
            result: Dict[str, Any] = self.zulip_client.send_message(
                {
                    "type": "stream",
                    "to": stream,
                    "subject": topic,
                    "content": content,
                }
            )
        except Exception as exception:
            # Generally raised when user is forbidden
            raise BridgeFatalZulipError(exception) from exception
        if result["result"] != "success":
            # Generally raised when API key is invalid
            raise BridgeFatalZulipError(result["msg"])

        # Update the bot's read marker in order to show the other users which
        # messages are already processed by the bot.
        await self.matrix_client.room_read_markers(
            room.room_id, fully_read_event=event.event_id, read_event=event.event_id
        )

    async def get_message_content_from_event(
        self,
        event: nio.Event,
        room: nio.MatrixRoom,
    ) -> Optional[str]:
        message: str
        sender: Optional[str] = room.user_name(event.sender)

        if isinstance(event, nio.RoomMemberEvent):
            if self.no_noise:
                return None
            # Join and leave events can be noisy. They are ignored by default.
            # To enable these events pass `no_noise` as `False` as the script argument
            message = event.state_key + " " + event.membership
        elif isinstance(event, nio.RoomMessageFormatted):
            message = event.body
        elif isinstance(event, nio.RoomMessageMedia):
            message = await self.handle_media(event)
        elif type(event) in self.non_formatted_messages:
            message = "sends " + self.non_formatted_messages[type(event)]
        elif isinstance(event, nio.MegolmEvent):
            message = "sends an encrypted message"
        elif isinstance(event, nio.UnknownEvent) and event.type == "m.reaction":
            return None
        else:
            message = "event: " + type(event).__name__

        return ZULIP_MESSAGE_TEMPLATE.format(username=sender, uid=event.sender, message=message)

    async def handle_media(self, event: nio.RoomMessageMedia) -> str:
        """Parse a nio.RoomMessageMedia event.

        Upload the media to zulip and build an appropriate message.
        """
        # Split the mxc uri in "server_name" and "media_id".
        mxc_match: Optional[Match[str]] = re.fullmatch("mxc://([^/]+)/([^/]+)", event.url)
        if mxc_match is None or len(mxc_match.groups()) != 2:
            return "[message from bridge: media could not be handled]"
        server_name, media_id = mxc_match.groups()

        download: Union[DownloadResponse, DownloadError] = await self.matrix_client.download(
            server_name, media_id
        )
        if isinstance(download, nio.DownloadError):
            return "[message from bridge: media could not be downloaded]"

        file_fake: BytesIO = BytesIO(download.body)
        # zulip.client.do_api_query() needs a name. TODO: hacky...
        file_fake.name = download.filename

        result: Dict[str, Any] = self.zulip_client.upload_file(file_fake)
        if result["result"] != "success":
            return "[message from bridge: media could not be uploaded]"

        message: str
        if download.filename:
            message = "[{}]({})".format(download.filename, result["uri"])
        else:
            message = result["uri"]

        return message

    async def matrix_join_rooms(self) -> None:
        for room_id in self.matrix_config["bridges"]:
            result: Union[JoinResponse, JoinError] = await self.matrix_client.join(room_id)
            if isinstance(result, nio.JoinError):
                raise BridgeFatalMatrixError(str(result))

    async def matrix_login(self) -> None:
        result: Union[LoginResponse, LoginError] = await self.matrix_client.login(
            self.matrix_config["password"]
        )
        if isinstance(result, nio.LoginError):
            raise BridgeFatalMatrixError(str(result))

    async def run(self) -> None:
        print("Starting message handler on Matrix client")

        # Set up event callback.
        self.matrix_client.add_event_callback(self._matrix_to_zulip, nio.Event)

        await self.matrix_client.sync_forever()


class ZulipToMatrix:
    """
    Zulip -> Matrix
    """

    def __init__(
        self,
        zulip_client: zulip.Client,
        zulip_config: Dict[str, Any],
        matrix_client: nio.AsyncClient,
    ) -> None:
        self.zulip_client: zulip.Client = zulip_client
        self.zulip_config: Dict[str, Any] = zulip_config
        self.matrix_client: nio.AsyncClient = matrix_client
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        # Precompute the url of the Zulip server, needed later.
        result: Dict[str, Any] = self.zulip_client.get_server_settings()
        if result["result"] != "success":
            raise BridgeFatalZulipError("cannot get server settings")
        self.server_url: str = result["realm_uri"]
        if not self.server_url.startswith(("http:", "https:")):
            raise ValueError("Unexpected server URL scheme")

    @classmethod
    async def create(
        cls,
        zulip_client: zulip.Client,
        zulip_config: Dict[str, Any],
        matrix_client: nio.AsyncClient,
    ) -> "ZulipToMatrix":
        zulip_to_matrix: "ZulipToMatrix" = cls(zulip_client, zulip_config, matrix_client)
        zulip_to_matrix.ensure_stream_membership()
        return zulip_to_matrix

    def _matrix_send(self, **kwargs: Any) -> None:
        """Wrapper for sending messages to the matrix server."""
        result: Union[Response, ErrorResponse] = asyncio.run_coroutine_threadsafe(
            self.matrix_client.room_send(**kwargs), self.loop
        ).result()
        if isinstance(result, nio.RoomSendError):
            raise BridgeFatalMatrixError(str(result))

    def _zulip_to_matrix(self, msg: Dict[str, Any]) -> None:
        logging.debug("_zulip_to_matrix; msg: %s", msg)

        room_id: Optional[str] = self.get_matrix_room_for_zulip_message(msg)
        if room_id is None:
            return

        sender: str = msg["sender_full_name"]
        content: str = MATRIX_MESSAGE_TEMPLATE.format(
            username=sender, uid=msg["sender_id"], message=msg["content"]
        )

        # Forward Zulip message to Matrix.
        self._matrix_send(
            room_id=room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": content},
        )

        # Get embedded files.
        files_to_send, media_success = asyncio.run_coroutine_threadsafe(
            self.handle_media(msg["content"]), self.loop
        ).result()

        if files_to_send:
            self._matrix_send(
                room_id=room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": "This message contains the following files:"},
            )
            for file in files_to_send:
                self._matrix_send(room_id=room_id, message_type="m.room.message", content=file)
        if not media_success:
            self._matrix_send(
                room_id=room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": "This message contained some files which could not be forwarded.",
                },
            )

    def ensure_stream_membership(self) -> None:
        """Ensure that the client is member of all necessary streams.

        Note that this may create streams if they do not exist and if
        the bot has enough rights to do so.
        """
        for stream, _ in self.zulip_config["bridges"]:
            result: Dict[str, Any] = self.zulip_client.get_stream_id(stream)
            if result["result"] == "error":
                raise BridgeFatalZulipError(f"cannot access stream '{stream}': {result}")
            if result["result"] != "success":
                raise BridgeFatalZulipError(f"cannot checkout stream id for stream '{stream}'")
            result = self.zulip_client.add_subscriptions(streams=[{"name": stream}])
            if result["result"] != "success":
                raise BridgeFatalZulipError(f"cannot subscribe to stream '{stream}': {result}")

    def get_matrix_room_for_zulip_message(self, msg: Dict[str, Any]) -> Optional[str]:
        """Check whether we want to process the given message.

        Return the room to which the given message should be forwarded, or
        None if we do not want to process the given message.
        """
        if msg["type"] != "stream":
            return None

        # We do this to identify the messages generated from Matrix -> Zulip
        # and we make sure we don't forward it again to the Matrix.
        if msg["sender_email"] == self.zulip_config["email"]:
            return None

        key: Tuple[str, str] = (msg["display_recipient"], msg["subject"])
        if key not in self.zulip_config["bridges"]:
            return None

        return self.zulip_config["bridges"][key]

    async def handle_media(self, msg: str) -> Tuple[Optional[List[Dict[str, Any]]], bool]:
        """Handle embedded media in the Zulip message.

        Download the linked files from the Zulip server and upload them
        to mthe matrix server.
        Return a tuple containing the list of the messages which need
        to be sent to the matrix room and a boolean flag indicating
        whether there have been files for which the download/upload part
        failed.
        """
        msgtype: str
        files_to_send: List[Dict[str, Any]] = []
        success: bool = True

        for file in re.findall(r"\[[^\[\]]*\]\((/user_uploads/[^\(\)]*)\)", msg):
            result: Dict[str, Any] = self.zulip_client.call_endpoint(file, method="GET")
            if result["result"] != "success":
                success = False
                continue

            try:
                with urllib.request.urlopen(self.server_url + result["url"]) as response:  # noqa: S310
                    file_content: bytes = response.read()
                    mimetype: str = response.headers.get_content_type()
            except Exception:
                success = False
                continue

            filename: str = file.split("/")[-1]

            response, _ = await self.matrix_client.upload(
                data_provider=BytesIO(file_content), content_type=mimetype, filename=filename
            )
            if isinstance(response, nio.UploadError):
                success = False
                continue

            if mimetype.startswith("audio/"):
                msgtype = "m.audio"
            elif mimetype.startswith("image/"):
                msgtype = "m.image"
            elif mimetype.startswith("video/"):
                msgtype = "m.video"
            else:
                msgtype = "m.file"

            files_to_send.append(
                {
                    "body": filename,
                    "info": {"mimetype": mimetype},
                    "msgtype": msgtype,
                    "url": response.content_uri,
                }
            )

        return (files_to_send, success)

    async def run(self) -> None:
        print("Starting message handler on Zulip client")

        self.loop = asyncio.get_event_loop()

        with ThreadPoolExecutor() as executor:
            await asyncio.get_event_loop().run_in_executor(
                executor, self.zulip_client.call_on_each_message, self._zulip_to_matrix
            )


def die(*_: Any) -> None:
    # We actually want to exit, so run os._exit (so as not to be caught and restarted)
    os._exit(1)


def exception_handler(loop: asyncio.AbstractEventLoop, context: Dict[str, Any]) -> None:
    loop.default_exception_handler(context)
    os._exit(1)


def generate_parser() -> argparse.ArgumentParser:
    description: str = """
    Bridge between Zulip topics and Matrix channels.

    Example matrix 'room_id' options might be, if via matrix.org:
        * #zulip:matrix.org (zulip channel on Matrix)
        * #freenode_#zulip:matrix.org (zulip channel on irc.freenode.net)"""

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-c", "--config", required=False, help="Path to the config file for the bridge."
    )
    parser.add_argument("-d", "--debug", action="store_true", help="debugging mode switch")
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
    parser.add_argument(
        "--show-join-leave",
        dest="no_noise",
        default=True,
        action="store_false",
        help="Enable IRC join/leave events.",
    )
    return parser


def read_configuration(config_file: str) -> Dict[str, Dict[str, Any]]:
    matrix_key_set: Set[str] = {"host", "mxid", "password"}
    matrix_bridge_key_set: Set[str] = {"room_id"}
    matrix_full_key_set: Set[str] = matrix_key_set | matrix_bridge_key_set
    zulip_key_set: Set[str] = {"email", "api_key", "site"}
    zulip_bridge_key_set: Set[str] = {"stream", "topic"}
    zulip_full_key_set: Set[str] = zulip_key_set | zulip_bridge_key_set
    bridge_key_set: Set[str] = {"room_id", "stream", "topic"}

    config: configparser.ConfigParser = configparser.ConfigParser()

    try:
        config.read(config_file)
    except configparser.Error as exception:
        raise BridgeConfigError(str(exception)) from exception

    if set(config.sections()) < {"matrix", "zulip"}:
        raise BridgeConfigError("Please ensure the configuration has zulip & matrix sections.")

    result: Dict[str, Dict[str, Any]] = {"matrix": {}, "zulip": {}}
    # For Matrix: create a mapping with the Matrix room_ids as keys and
    # the corresponding (stream, topic) tuple as value.
    result["matrix"]["bridges"] = {}
    # For Zulip: create a mapping with the tuple (stream, topic) as keys
    # and the corresponding Matrix room_id as value.
    result["zulip"]["bridges"] = {}
    # One (and maybe the only) bridge is configured in the matrix/zulip
    # sections to keep backwards compatibility with older configuration
    # files.
    first_bridge: Dict[str, Any] = {}
    # Represent a (stream,topic) tuple.
    zulip_target: Tuple[str, str]

    for section in config.sections():
        section_config: Dict[str, str] = dict(config[section])
        section_keys: Set[str] = set(section_config.keys())

        if section.startswith("additional_bridge"):
            if section_keys != bridge_key_set:
                raise BridgeConfigError(
                    f"Please ensure the bridge configuration section {section} contain the following keys: {bridge_key_set}."
                )

            zulip_target = (section_config["stream"], section_config["topic"])
            result["zulip"]["bridges"][zulip_target] = section_config["room_id"]
            result["matrix"]["bridges"][section_config["room_id"]] = zulip_target
        elif section == "matrix":
            if section_keys != matrix_full_key_set:
                raise BridgeConfigError(
                    "Please ensure the matrix configuration section contains the following keys: %s."
                    % str(matrix_full_key_set)
                )

            result["matrix"].update({key: section_config[key] for key in matrix_key_set})

            for key in matrix_bridge_key_set:
                first_bridge[key] = section_config[key]

            # Verify the format of the Matrix user ID.
            if re.fullmatch(r"@[^:]+:.+", result["matrix"]["mxid"]) is None:
                raise BridgeConfigError("Malformatted mxid.")
        elif section == "zulip":
            if section_keys != zulip_full_key_set:
                raise BridgeConfigError(
                    "Please ensure the zulip configuration section contains the following keys: %s."
                    % str(zulip_full_key_set)
                )

            result["zulip"].update({key: section_config[key] for key in zulip_key_set})

            for key in zulip_bridge_key_set:
                first_bridge[key] = section_config[key]
        else:
            logging.warning("Unknown section %s", section)

    # Add the "first_bridge" to the bridges.
    zulip_target = (first_bridge["stream"], first_bridge["topic"])
    result["zulip"]["bridges"][zulip_target] = first_bridge["room_id"]
    result["matrix"]["bridges"][first_bridge["room_id"]] = zulip_target

    return result


async def run(zulip_config: Dict[str, Any], matrix_config: Dict[str, Any], no_noise: bool) -> None:
    asyncio.get_event_loop().set_exception_handler(exception_handler)

    matrix_client: Optional[nio.AsyncClient] = None

    print("Starting Zulip <-> Matrix mirroring bot")

    # Initiate clients and start the event listeners.
    backoff = zulip.RandomExponentialBackoff(timeout_success_equivalent=300)
    while backoff.keep_going():
        try:
            zulip_client = zulip.Client(
                email=zulip_config["email"],
                api_key=zulip_config["api_key"],
                site=zulip_config["site"],
            )
            matrix_client = nio.AsyncClient(matrix_config["host"], matrix_config["mxid"])

            matrix_to_zulip: MatrixToZulip = await MatrixToZulip.create(
                matrix_client, matrix_config, zulip_client, no_noise
            )
            zulip_to_matrix: ZulipToMatrix = await ZulipToMatrix.create(
                zulip_client, zulip_config, matrix_client
            )

            await asyncio.gather(matrix_to_zulip.run(), zulip_to_matrix.run())

        except BridgeFatalMatrixError as exception:
            sys.exit(f"Matrix bridge error: {exception}")
        except BridgeFatalZulipError as exception:
            sys.exit(f"Zulip bridge error: {exception}")
        except zulip.ZulipError as exception:
            sys.exit(f"Zulip error: {exception}")
        except Exception:
            traceback.print_exc()
        finally:
            if matrix_client:
                await matrix_client.close()
        backoff.fail()


def write_sample_config(target_path: str, zuliprc: Optional[str]) -> None:
    if os.path.exists(target_path):
        raise BridgeConfigError(f"Path '{target_path}' exists; not overwriting existing file.")

    sample_dict: OrderedDict[str, OrderedDict[str, str]] = OrderedDict(
        (
            (
                "matrix",
                OrderedDict(
                    (
                        ("host", "https://matrix.org"),
                        ("mxid", "@username:matrix.org"),
                        ("password", "password"),
                        ("room_id", "#zulip:matrix.org"),
                    )
                ),
            ),
            (
                "zulip",
                OrderedDict(
                    (
                        ("email", "glitch-bot@chat.zulip.org"),
                        ("api_key", "aPiKeY"),
                        ("site", "https://chat.zulip.org"),
                        ("stream", "test here"),
                        ("topic", "matrix"),
                    )
                ),
            ),
            (
                "additional_bridge1",
                OrderedDict(
                    (
                        ("room_id", "#example:matrix.org"),
                        ("stream", "new test"),
                        ("topic", "matrix"),
                    )
                ),
            ),
        )
    )

    if zuliprc is not None:
        if not os.path.exists(zuliprc):
            raise BridgeConfigError(f"Zuliprc file '{zuliprc}' does not exist.")

        zuliprc_config: configparser.ConfigParser = configparser.ConfigParser()
        try:
            zuliprc_config.read(zuliprc)
        except configparser.Error as exception:
            raise BridgeConfigError(str(exception)) from exception

        try:
            sample_dict["zulip"]["email"] = zuliprc_config["api"]["email"]
            sample_dict["zulip"]["site"] = zuliprc_config["api"]["site"]
            sample_dict["zulip"]["api_key"] = zuliprc_config["api"]["key"]
        except KeyError as exception:
            raise BridgeConfigError(
                "You provided an invalid zuliprc file: " + str(exception)
            ) from exception

    sample: configparser.ConfigParser = configparser.ConfigParser()
    sample.read_dict(sample_dict)
    with open(target_path, "w") as target:
        sample.write(target)


def main() -> None:
    signal.signal(signal.SIGINT, die)
    signal.signal(signal.SIGTERM, die)
    logging.basicConfig(level=logging.WARNING)

    parser: argparse.ArgumentParser = generate_parser()
    options: argparse.Namespace = parser.parse_args()

    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if options.sample_config:
        try:
            write_sample_config(options.sample_config, options.zuliprc)
        except BridgeConfigError as exception:
            print(f"Could not write sample config: {exception}")
            sys.exit(1)
        if options.zuliprc is None:
            print(f"Wrote sample configuration to '{options.sample_config}'")
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
        config: Dict[str, Dict[str, Any]] = read_configuration(options.config)
    except BridgeConfigError as exception:
        print(f"Could not parse config file: {exception}")
        sys.exit(1)

    # Get config for each client
    zulip_config: Dict[str, Any] = config["zulip"]
    matrix_config: Dict[str, Any] = config["matrix"]

    loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
    loop.run_until_complete(run(zulip_config, matrix_config, options.no_noise))
    loop.close()


if __name__ == "__main__":
    main()

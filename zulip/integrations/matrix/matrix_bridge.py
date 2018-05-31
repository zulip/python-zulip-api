#!/usr/bin/env python
import os
import logging
import signal
import traceback
import zulip
import sys
import argparse
import re

from types import FrameType
from typing import Any, Callable, Dict, Optional

from matrix_bridge_config import config
from matrix_client.api import MatrixRequestError
from matrix_client.client import MatrixClient
from requests.exceptions import MissingSchema

GENERAL_NETWORK_USERNAME_REGEX = '@_?[a-zA-Z0-9]+_([a-zA-Z0-9-_]+):[a-zA-Z0-9.]+'
MATRIX_USERNAME_REGEX = '@([a-zA-Z0-9-_]+):matrix.org'

# change these templates to change the format of displayed message
ZULIP_MESSAGE_TEMPLATE = "**{username}**: {message}"
MATRIX_MESSAGE_TEMPLATE = "<{username}> {message}"

def matrix_login(matrix_client: Any, matrix_config: Dict[str, Any]) -> None:
    try:
        matrix_client.login_with_password(matrix_config["username"],
                                          matrix_config["password"])
    except MatrixRequestError as e:
        if e.code == 403:
            sys.exit("Bad username or password.")
        else:
            sys.exit("Check if your server details are correct.")
    except MissingSchema as e:
        sys.exit("Bad URL format.")

def matrix_join_room(matrix_client: Any, matrix_config: Dict[str, Any]) -> Any:
    try:
        room = matrix_client.join_room(matrix_config["room_id"])
        return room
    except MatrixRequestError as e:
        if e.code == 403:
            sys.exit("Room ID/Alias in the wrong format")
        else:
            sys.exit("Couldn't find room.")

def die(signal: int, frame: FrameType) -> None:
    # We actually want to exit, so run os._exit (so as not to be caught and restarted)
    os._exit(1)

def matrix_to_zulip(zulip_client: zulip.Client, zulip_config: Dict[str, Any],
                    matrix_config: Dict[str, Any],
                    no_noise: bool) -> Callable[[Any, Dict[str, Any]], None]:
    def _matrix_to_zulip(room: Any, event: Dict[str, Any]) -> None:
        """
        Matrix -> Zulip
        """
        content = get_message_content_from_event(event, no_noise)

        zulip_bot_user = ('@%s:matrix.org' % matrix_config['username'])
        # We do this to identify the messages generated from Zulip -> Matrix
        # and we make sure we don't forward it again to the Zulip stream.
        not_from_zulip_bot = ('body' not in event['content'] or
                              event['sender'] != zulip_bot_user)

        if not_from_zulip_bot and content:
            try:
                result = zulip_client.send_message({
                    "sender": zulip_client.email,
                    "type": "stream",
                    "to": zulip_config["stream"],
                    "subject": zulip_config["topic"],
                    "content": content,
                })
            except MatrixRequestError as e:
                # Generally raised when user is forbidden
                raise Exception(e)
            if result['result'] != 'success':
                # Generally raised when API key is invalid
                raise Exception(result['msg'])

    return _matrix_to_zulip

def get_message_content_from_event(event: Dict[str, Any], no_noise: bool) -> Optional[str]:
    irc_nick = shorten_irc_nick(event['sender'])
    if event['type'] == "m.room.member":
        if no_noise:
            return None
        # Join and leave events can be noisy. They are ignored by default.
        # To enable these events pass `no_noise` as `False` as the script argument
        if event['membership'] == "join":
            content = ZULIP_MESSAGE_TEMPLATE.format(username=irc_nick,
                                                    message="joined")
        elif event['membership'] == "leave":
            content = ZULIP_MESSAGE_TEMPLATE.format(username=irc_nick,
                                                    message="quit")
    elif event['type'] == "m.room.message":
        if event['content']['msgtype'] == "m.text" or event['content']['msgtype'] == "m.emote":
            content = ZULIP_MESSAGE_TEMPLATE.format(username=irc_nick,
                                                    message=event['content']['body'])
    else:
        content = event['type']
    return content

def shorten_irc_nick(nick: str) -> str:
    """
    Add nick shortner functions for specific IRC networks
    Eg: For freenode change '@freenode_user:matrix.org' to 'user'
    Check the list of IRC networks here:
    https://github.com/matrix-org/matrix-appservice-irc/wiki/Bridged-IRC-networks
    """
    match = re.match(GENERAL_NETWORK_USERNAME_REGEX, nick)
    if match:
        return match.group(1)
    # For matrix users
    match = re.match(MATRIX_USERNAME_REGEX, nick)
    if match:
        return match.group(1)
    return nick

def zulip_to_matrix(config: Dict[str, Any], room: Any) -> Callable[[Dict[str, Any]], None]:

    def _zulip_to_matrix(msg: Dict[str, Any]) -> None:
        """
        Zulip -> Matrix
        """
        message_valid = check_zulip_message_validity(msg, config)
        if message_valid:
            matrix_username = msg["sender_full_name"].replace(' ', '')
            matrix_text = MATRIX_MESSAGE_TEMPLATE.format(username=matrix_username,
                                                         message=msg["content"])
            # Forward Zulip message to Matrix
            room.send_text(matrix_text)
    return _zulip_to_matrix

def check_zulip_message_validity(msg: Dict[str, Any], config: Dict[str, Any]) -> bool:
    is_a_stream = msg["type"] == "stream"
    in_the_specified_stream = msg["display_recipient"] == config["stream"]
    at_the_specified_subject = msg["subject"] == config["topic"]

    # We do this to identify the messages generated from Matrix -> Zulip
    # and we make sure we don't forward it again to the Matrix.
    not_from_zulip_bot = msg["sender_email"] != config["email"]
    if is_a_stream and not_from_zulip_bot and in_the_specified_stream and at_the_specified_subject:
        return True
    return False

def parse_args():
    # type: () -> Any
    parser = argparse.ArgumentParser()
    parser.add_argument('--no_noise',
                        default=True,
                        help="Suppress the IRC join/leave events.")
    return parser.parse_args()

def main() -> None:
    signal.signal(signal.SIGINT, die)
    logging.basicConfig(level=logging.WARNING)

    # Get config for each clients
    zulip_config = config["zulip"]
    matrix_config = config["matrix"]

    options = parse_args()

    # Initiate clients
    backoff = zulip.RandomExponentialBackoff(timeout_success_equivalent=300)
    while backoff.keep_going():
        print("Starting matrix mirroring bot")
        try:
            zulip_client = zulip.Client(email=zulip_config["email"],
                                        api_key=zulip_config["api_key"],
                                        site=zulip_config["site"])
            matrix_client = MatrixClient(matrix_config["host"])

            # Login to Matrix
            matrix_login(matrix_client, matrix_config)
            # Join a room in Matrix
            room = matrix_join_room(matrix_client, matrix_config)

            room.add_listener(matrix_to_zulip(zulip_client, zulip_config, matrix_config,
                                              options.no_noise))

            print("Starting listener thread on Matrix client")
            matrix_client.start_listener_thread()

            print("Starting message handler on Zulip client")
            zulip_client.call_on_each_message(zulip_to_matrix(zulip_config, room))
        except Exception:
            traceback.print_exc()
        backoff.fail()

if __name__ == '__main__':
    main()

#!/usr/bin/env python

import os
import logging
import signal
import traceback

from types import FrameType
from typing import Any, Callable, Dict

from matrix_bridge_config import config
import zulip
from matrix_client.client import MatrixClient

def die(signal: int, frame: FrameType) -> None:
    # We actually want to exit, so run os._exit (so as not to be caught and restarted)
    os._exit(1)

def zulip_to_matrix_username(full_name: str, site: str) -> str:
    return "@**{0}**:{1}".format(full_name, site)

def matrix_to_zulip(zulip_client: zulip.Client,
                    cfg: Dict[str, Any]) -> Callable[[Any, Dict[str, Any]], None]:
    def _matrix_to_zulip(room: Any, event: Dict[str, Any]) -> None:
        """Matrix -> Zulip
        """
        if event['type'] == "m.room.member":
            if event['membership'] == "join":
                content = "{0} joined".format(event['content']['displayname'])
        elif event['type'] == "m.room.message":
            if event['content']['msgtype'] == "m.text":
                content = "{0}: {1}".format(event['sender'], event['content']['body'])
        else:
            content = event['type']
        not_from_bot = ('body' not in event['content'] or
                        not event['content']['body'].startswith("@**"))
        if not_from_bot:
            print(zulip_client.send_message({
                "sender": zulip_client.email,
                "type": "stream",
                "to": cfg["stream"],
                "subject": cfg["subject"],
                "content": content,
            }))
    return _matrix_to_zulip

def zulip_to_matrix(cfg: Dict[str, Any], room: Any) -> Callable[[Dict[str, Any]], None]:
    site_without_http = cfg["site"].replace("https://", "").replace("http://", "")

    def _zulip_to_matrix(msg: Dict[str, Any]) -> None:
        """Zulip -> Matrix
        """
        isa_stream = msg["type"] == "stream"
        not_from_bot = msg["sender_email"] != cfg["email"]
        in_the_specified_stream = msg["display_recipient"] == cfg["stream"]
        at_the_specified_subject = msg["subject"] == cfg["subject"]
        if isa_stream and not_from_bot and in_the_specified_stream and at_the_specified_subject:
            matrix_username = zulip_to_matrix_username(msg["sender_full_name"], site_without_http)
            matrix_text = "{0}: {1}".format(matrix_username,
                                            msg["content"])
            print(matrix_text)
            room.send_text(matrix_text)
    return _zulip_to_matrix

if __name__ == '__main__':
    signal.signal(signal.SIGINT, die)
    logging.basicConfig(level=logging.WARNING)

    # Get config for each clients
    zulip_config = config["zulip"]
    matrix_config = config["matrix"]

    # Initiate clients
    backoff = zulip.RandomExponentialBackoff(timeout_success_equivalent=300)
    while backoff.keep_going():
        print("Starting matrix mirroring bot")
        try:
            zulip_client = zulip.Client(email=zulip_config["email"],
                                        api_key=zulip_config["api_key"],
                                        site=zulip_config["site"])
            matrix_client = MatrixClient(matrix_config["host"])

            # TODO this lacks the proper error handling
            matrix_client.login_with_password(matrix_config["username"],
                                              matrix_config["password"])
            room = matrix_client.join_room(matrix_config["room_id"])
            room.add_listener(matrix_to_zulip(zulip_client, zulip_config))

            print("Starting listener thread on Matrix client")
            matrix_client.start_listener_thread()

            print("Starting message handler on Zulip client")
            zulip_client.call_on_each_message(zulip_to_matrix(zulip_config, room))
        except Exception:
            traceback.print_exc()
        backoff.fail()

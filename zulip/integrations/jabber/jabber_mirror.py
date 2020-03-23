#!/usr/bin/env python

from __future__ import print_function
import sys
import subprocess
import os
import traceback
import signal
from types import FrameType
from typing import Any
from zulip import RandomExponentialBackoff

def die(signal, frame):
    # type: (int, FrameType) -> None
    """We actually want to exit, so run os._exit (so as not to be caught and restarted)"""
    os._exit(1)

signal.signal(signal.SIGINT, die)

args = [os.path.join(os.path.dirname(sys.argv[0]), "jabber_mirror_backend.py")]
args.extend(sys.argv[1:])

backoff = RandomExponentialBackoff(timeout_success_equivalent=300)
while backoff.keep_going():
    print("Starting Jabber mirroring bot")
    try:
        ret = subprocess.call(args)
    except Exception:
        traceback.print_exc()
    else:
        if ret == 2:
            # Don't try again on initial configuration errors
            sys.exit(ret)

    backoff.fail()

print("")
print("")
print("ERROR: The Jabber mirroring bot is unable to continue mirroring Jabber.")
print("Please contact zulip-devel@googlegroups.com if you need assistance.")
print("")
sys.exit(1)

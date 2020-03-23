#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function
import sys
import subprocess
import os
import traceback
import signal

sys.path[:0] = [os.path.dirname(__file__)]
from zephyr_mirror_backend import parse_args

(options, args) = parse_args()

from types import FrameType
from typing import Any

def die(signal, frame):
    # type: (int, FrameType) -> None

    # We actually want to exit, so run os._exit (so as not to be caught and restarted)
    os._exit(1)

signal.signal(signal.SIGINT, die)

from zulip import RandomExponentialBackoff

args = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "zephyr_mirror_backend.py")]
args.extend(sys.argv[1:])

if options.sync_subscriptions:
    subprocess.call(args)
    sys.exit(0)

if options.forward_class_messages and not options.noshard:
    # Needed to get access to zephyr.lib.parallel
    sys.path.append("/home/zulip/zulip")
    if options.on_startup_command is not None:
        subprocess.call([options.on_startup_command])
    from zerver.lib.parallel import run_parallel
    print("Starting parallel zephyr class mirroring bot")
    jobs = list("0123456789abcdef")

    def run_job(shard):
        # type: (str) -> int
        subprocess.call(args + ["--shard=%s" % (shard,)])
        return 0
    for (status, job) in run_parallel(run_job, jobs, threads=16):
        print("A mirroring shard died!")
        pass
    sys.exit(0)

backoff = RandomExponentialBackoff(timeout_success_equivalent=300)
while backoff.keep_going():
    print("Starting zephyr mirroring bot")
    try:
        subprocess.call(args)
    except Exception:
        traceback.print_exc()
    backoff.fail()


error_message = """
ERROR: The Zephyr mirroring bot is unable to continue mirroring Zephyrs.
This is often caused by failing to maintain unexpired Kerberos tickets
or AFS tokens.  See https://zulipchat.com/zephyr for documentation on how to
maintain unexpired Kerberos tickets and AFS tokens.
"""
print(error_message)
sys.exit(1)

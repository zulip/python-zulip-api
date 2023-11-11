#!/usr/bin/env python3

import asyncio
import os
import signal
import subprocess
import sys
import traceback
from types import FrameType
from typing import Optional

sys.path[:0] = [os.path.dirname(__file__)]
from zephyr_mirror_backend import parse_args

options, args = parse_args()


def die(signal: int, frame: Optional[FrameType]) -> None:
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
    if options.on_startup_command is not None:
        subprocess.call([options.on_startup_command])

    print("Starting parallel zephyr class mirroring bot")
    shards = list("0123456789abcdef")

    async def run_shard(shard: str) -> int:
        process = await asyncio.create_subprocess_exec(*args, f"--shard={shard}")
        return await process.wait()

    async def run_shards() -> None:
        for coro in asyncio.as_completed(map(run_shard, shards)):
            await coro
            print("A mirroring shard died!")

    asyncio.run(run_shards())
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
or AFS tokens.  See https://zulip.com/zephyr for documentation on how to
maintain unexpired Kerberos tickets and AFS tokens.
"""
print(error_message)
sys.exit(1)

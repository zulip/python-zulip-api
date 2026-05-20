#!/usr/bin/env python3

import re
from typing import Any, Dict

import requests

from zulip_bots.lib import AbstractBotHandler

import argparse
import json
import os
import sys
import urllib.parse
from configparser import ConfigParser
from typing import Any, Dict

from litellm import completion  # type: ignore[import-not-found]

import zulip


def format_conversation(result: Dict[str, Any]) -> str:
    # Note: Including timestamps seems to have no impact; including reactions
    # makes the results worse.
    zulip_messages = result["messages"]
    if len(zulip_messages) == 0:
        print("No messages in conversation to summarize")
        sys.exit(0)

    zulip_messages_list = [
        {"sender": f'@_**{message["sender_full_name"]}**', "content": message["content"]}
        for message in zulip_messages
    ]
    return json.dumps(zulip_messages_list)


def make_message(content: str, role: str = "user") -> Dict[str, str]:
    return {"content": content, "role": role}


def get_max_summary_length(conversation_length: int) -> int:
    return min(6, 4 + int((conversation_length - 10) / 10))


config_file = "/home/tabbott/zuliprc-llm"
if not config_file:
    print("Could not find the Zulip configuration file. Please read the provided README.")
    sys.exit()

client = zulip.Client(config_file=config_file)

config = ConfigParser()
# Make config parser case sensitive otherwise API keys will be lowercased
# which is not supported by litellm.
# https://docs.python.org/3/library/configparser.html#configparser.ConfigParser.optionxform
config.optionxform = str  # type: ignore[assignment, method-assign]

with open(config_file) as f:
    config.read_file(f, config_file)

# Set all the keys in `litellm` as environment variables.
for key in config["litellm"]:
    print("Setting key:", key)
    os.environ[key] = config["litellm"][key]

from dataclasses import dataclass


class LLMArgs:
    max_tokens: int = 600
    max_messages: int = 100
    # gpt-4.1 gpt-4o-mini gpt-4.1-mini o4-mini
    model: str = "gpt-4.1-mini"


args = LLMArgs()


def summarize_conversation(channel: str, topic: str) -> str:
    model = args.model

    narrow = [
        {"operator": "channel", "operand": channel},
        {"operator": "topic", "operand": topic},
    ]

    request = {
        "anchor": "newest",
        "num_before": args.max_messages,
        "num_after": 0,
        "narrow": narrow,
        # Fetch raw Markdown, not HTML
        "apply_markdown": False,
    }
    result = client.get_messages(request)
    if result["result"] == "error":
        print("Failed fetching message history", result)
        sys.exit(1)

    conversation_length = len(result["messages"])
    max_summary_length = get_max_summary_length(conversation_length)

    print(f"Max summary length: {max_summary_length}")

    intro = f"The following is a chat conversation in the Zulip team chat app. channel: {channel}, topic: {topic}"
    formatted_conversation = format_conversation(result)
    prompt = f"Succinctly summarize this conversation based only on the information provided, in up to {max_summary_length} sentences, for someone who is familiar with the context. Mention key conclusions and actions, if any. Refer to specific people as appropriate, formatting names with this special syntax: Tim Abbott should be formatted as @_**Tim Abbott**. Don't use an intro phrase. You can use Zulip's CommonMark based formatting. Please use paragraph breaks after every 2-3 sentences."
    messages = [
        make_message(intro, "system"),
        make_message(formatted_conversation),
        make_message(prompt),
    ]

    # Send formatted messages to the LLM model for summarization
    response = completion(
        max_tokens=args.max_tokens,
        model=model,
        messages=messages,
    )

    print(
        f"Used {response['usage']['completion_tokens']} completion tokens to summarize {conversation_length} Zulip messages ({response['usage']['prompt_tokens']} prompt tokens)."
    )
    print()
    return response["choices"][0]["message"]["content"]


class LiteLLMHandler:
    """A Zulip bot handler for LLMs"""

    def usage(self) -> str:
        return ""

    def initialize(self, bot_handler: AbstractBotHandler) -> None:
        pass

    def handle_message(self, message: Dict[str, str], bot_handler: AbstractBotHandler) -> None:
        content = message["content"].strip("#*")
        channel, topic = content.split(">", 1)
        print(channel, topic)

        response = summarize_conversation(channel, topic)

        bot_handler.send_reply(message, response)


handler_class = LiteLLMHandler

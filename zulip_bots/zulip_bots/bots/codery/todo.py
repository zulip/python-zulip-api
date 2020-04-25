import sys
import os
sys.path.insert(0, os.getcwd())

import copy
import importlib
import random
from math import log10, floor

import re
from converter import utils
from typing import Any, Dict, List

'''
class todo(object):

	def usage(self) -> str:
		return "This plugin is a ToDo App"

	def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
		bot_response = self.get_todo_response(message, bot_handler)
		bot_handler.send_reply(message, bot_response)

handler_class = todo
'''


def get_todo_response(content, bot_handler: Any) -> str:
    
    words = content.split()
    print(words)
    if words[1] == "start":
        bot_handler.storage.put("list", "")
        return "todo initialized"
    if words[1] == "list":
        res = bot_handler.storage.get("list")
        val = ""
        values = res.split("~")
        i = 1
        for temp in values:
            val = val + str(i) + ". " + temp + "\n"
            i += 1
        return val
    elif words[1] == "add":
        res = bot_handler.storage.get("list")
        res = res + " ".join(words[2::]) + "~"
        bot_handler.storage.put("list", res)
        return "Added to list."
    elif words[1] == "remove":
        index = int(words[2])
        res = bot_handler.storage.get("list")
        val = ""
        values = res.split("~")
        i = 1
        for temp in values:
            if i != index:
                val = val + temp + "~"
            i += 1
        bot_handler.storage.put("list", val)
        return "Removed from list."

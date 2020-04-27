import sys
import os
sys.path.insert(0, os.getcwd())

import requests
from typing import Any
def get_joke(content, bot_handler: Any) -> str:
    words = content.lower().split()
    print(words)
    joke = requests.get('https://geek-jokes.sameerkumar.website/api?format=json').json()
    res = ""
    res = joke["joke"]
    return res

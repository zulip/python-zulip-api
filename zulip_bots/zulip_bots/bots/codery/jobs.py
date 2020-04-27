import sys
import os
sys.path.insert(0, os.getcwd())

import requests
from typing import Any
def get_jobs(content, bot_handler: Any) -> str:
    words = content.lower().split()
    print(words)
    jobs = requests.get('https://jobs.github.com/positions.json?description=' + words[1]).json()
    res = ""
    i = 1
    for job in jobs:
        res = res + job['title'] + "\n" + job['url'] + "\n\n"
        i += 1
        if i == 5:
            break
    return res

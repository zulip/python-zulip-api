import sys
import os
import config
sys.path.insert(0, os.getcwd())
import requests
from typing import Any
from typing import Dict
from typing import List
from pyudemy import Udemy


udemy = Udemy(config.CLIENT_ID, config.CLIENT_SECRET)

def get_courses(content, bot_handler: Any) -> str:

    courses = udemy.courses()

    print(courses)
    res = ""
    i = 1
    for course in courses['results']:
        res = res + course['title'] + "\n" + "https://www.udemy.com"+course['url'] + "\n" + course['price'] + "\n\n"
        i += 1
        if i == 5:
            break
    return res

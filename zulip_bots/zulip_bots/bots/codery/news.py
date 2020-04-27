import sys
import os
sys.path.insert(0, os.getcwd())
import requests
# import json
from typing import Any
def get_news_response(content, bot_handler: Any) -> str:
    words = content.lower().split()
    print(words)
    articles = requests.get('https://newsapi.org/v2/everything?q=' + words[1] + '&apiKey=142ba11e03d74ba38f859c785eee017f').json()
    res = ""
    i = 1
    for article in articles['articles']:
        res = res + article['title'] + "\n" + article['url'] + "\n\n"
        i += 1
        if i == 5:
            break
    return res

import sys, os
sys.path.insert(0,os.getcwd())

import requests
import json
from typing import Any,Dict,List
'''
class news(object):

	def usage(self) -> str:
		return "This plugin is a News App"

	def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
		bot_response = self.get_news_response(message, bot_handler)
		bot_handler.send_reply(message, bot_response)

handler_class = news
'''

def get_joke(content, bot_handler: Any) -> str:
	words = content.lower().split()
	print(words)
	joke = requests.get('https://geek-jokes.sameerkumar.website/api?format=json').json()
	res = "" 
	res=joke["joke"]
	return res



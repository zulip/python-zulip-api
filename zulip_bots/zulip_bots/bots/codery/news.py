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

def get_news_response(content, bot_handler: Any) -> str:
	words = content.lower().split()
	print(words)
	articles = requests.get('https://newsapi.org/v2/everything?q=' + words[1] + '&apiKey=142ba11e03d74ba38f859c785eee017f').json()
	res = "" 
	i = 1
	for article in articles['articles'] :
		res = res + article['title'] + "\n" + article['url'] + "\n\n"
		i += 1
		if i == 5 :
			break  
	return res



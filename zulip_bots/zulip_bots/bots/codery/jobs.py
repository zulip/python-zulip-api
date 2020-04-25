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

def get_jobs(content, bot_handler: Any) -> str:
	words = content.lower().split()
	print(words)
	
	jobs = requests.get('https://jobs.github.com/positions.json?description=' + words[1]).json()
	res = "" 
	i = 1
	for job in jobs :
		res = res + job['title'] + "\n" + job['url'] + "\n\n"
		i += 1
		if i == 5 :
			break  
	return res




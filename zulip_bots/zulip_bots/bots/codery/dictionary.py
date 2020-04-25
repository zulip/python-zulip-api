from PyDictionary import PyDictionary
from typing import Any, Dict, List
'''
class dictionary(object):

	def usage(self) -> str:
		return "This plugin is a News App"

	def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
		bot_response = self.get_dictionary_response(message, bot_handler)
		bot_handler.send_reply(message, bot_response)

handler_class = dictionary
'''

def get_dictionary_response(content, bot_handler: Any) -> str:
	
	words = content.lower().split()
	dictionary=PyDictionary()
	res = dictionary.meaning(words[1])
	if res != None:
		res = res['Noun']
		ans = ""
		for i in res:
			ans = ans + i + "\n\n"
		return ans
	return "Unable to find meaning :("
import sys, os
sys.path.insert(0,os.getcwd())

import copy
import importlib
import random
from math import log10, floor

import re
from converter import utils

from typing import Any, Dict, List

'''
class calculator(object):

	def usage(self) -> str:
		return 'This plugin is a Calculator.'
	def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
		bot_response = self.get_calculator_response(message, bot_handler)
		bot_handler.send_reply(message, bot_response)

handler_class = calculator
'''

def get_calculator_response(content, bot_handler: Any) -> str:
	words = content.lower().split()
	print(words)
	if words[2] == "+" :
		temp = float(words[1]) 
		temp1 = float(words[3])
		temp = temp + temp1 
		return str( temp ) 
	elif words[2] == "-" :
		temp = float(words[1]) 
		temp1 = float(words[3])
		temp = temp - temp1 
		return str( temp )
	elif words[2] == "*" :
		temp = float(words[1]) 
		temp1 = float(words[3])
		temp = temp * temp1 
		return str( temp )
	elif words[2] == "/" :
		if words[3] == "0":
			return "Division by zero."
		temp = float(words[1]) 
		temp1 = float(words[3])
		temp = temp / temp1 
		return str( temp )
	else :
		return "Please apply spaces after each number of mathematical operator"
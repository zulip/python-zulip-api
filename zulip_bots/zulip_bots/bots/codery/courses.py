import sys, os
import config
sys.path.insert(0,os.getcwd())

import requests
import json
from typing import Any,Dict,List

import logging
from urllib import parse
from pyudemy import Udemy
import requests

from bs4 import BeautifulSoup

from typing import Dict, Any, Union, List

udemy = Udemy(config.CLIENT_ID, config.CLIENT_SECRET)

def get_courses(content, bot_handler: Any) -> str:
	
	courses = udemy.courses()

	print(courses)
	
	
	res = "" 
	i = 1
	for course in courses['results'] :
		res = res + course['title'] + "\n" + "https://www.udemy.com"+course['url'] + "\n" + course['price']+ "\n\n"
		i += 1
		if i == 5 :
			break  
	return res




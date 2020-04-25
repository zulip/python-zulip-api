import requests
from bs4 import BeautifulSoup


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import Any
from webdriver_manager.chrome import ChromeDriverManager
chrome_options = Options()  
chrome_options.add_argument("--headless") 
path=ChromeDriverManager().install()

driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=path)

import sys, os
sys.path.insert(0,os.getcwd())

def get_leaderboard() -> str:

    driver.get("https://www.stopstalk.com/leaderboard")
    l=[]
    i=0

    for tr in driver.find_elements_by_tag_name("tr"):
        l.append("##")
        for td in tr.find_elements_by_tag_name("td"):
            if i>8:
                l.append(td.get_attribute("innerText") + "@@")
        i+=1

    l1=""
    for r in l:
        allC = r.split("##")
        for eachC in allC:
            attrList = eachC.split("@@")
            for attr in attrList:
                l1+=attr+"\n"

    return(l1.strip())


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
chrome_options = Options()
chrome_options.add_argument("--headless")
path = ChromeDriverManager().install()

driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=path)

import sys
import os
sys.path.insert(0, os.getcwd())

def get_problems() -> str:

    driver.get("https://www.stopstalk.com/problems/trending")
    lo = []
    i = 0

    for tr in driver.find_elements_by_tag_name("tr"):
        lo.append("##")
        for td in tr.find_elements_by_tag_name("td"):
            if i > 8:
                lo.append(td.get_attribute("innerText") + "@@")
        i += 1

    l1 = ""
    for r in lo:
        allC = r.split("##")
        for eachC in allC:
            attrList = eachC.split("@@")
            for attr in attrList:
                l1 += attr+"\n"

    return(l1.strip())

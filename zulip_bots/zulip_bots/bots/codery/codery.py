# See readme.md for instructions on running this code.
import logging
from urllib import parse
import sys, os, zulip
sys.path.insert(0,os.getcwd())

import requests
import calculator,todo, dictionary,news,geekjokes,courses, jobs, leaderboard,trendingproblems
from bs4 import BeautifulSoup

from typing import Dict, Any, Union, List


def get_codery_result(codery_keywords: str) -> str:
    help_message = "*Help for Codery*  : \n\n" \
                   "The bot responds to messages starting with @Codery.\n\n" \
                   "`@Codery contests` will return top Contests today, their dates, time left and the links to each contest.\n" \
                   "`@Codery top contest` also returns the top Contest result.\n" \
                   "`@Codery trending` returns the top trending ploblems across all programming platforms.\n" \
                   "`@Codery dictionary <search term>` returns the meaning of that word in an instant.\n" \
                   "`@Codery jokes` keeps your morale boosted with programming jokes.\n" \
                   "`@Codery jobs <searchword>` returns the top jobs for that search word.\n" \
                   "`@Codery news <keyword>` returns the news for that key word.\n" \
                   "`@Codery man <function>` returns the user manual of that function.\n" \
                   "`@Codery top <n> contests` will return n number of top contests at that time.\n \n" \
                   "Example:\n" \
                   " * @Codery contests\n" \
                   " * @Codery top contest\n" \
                   " * @Codery jokes\n" \
                   " * @Codery top 7 contests\n" \
                   " * @Codery dictionary computer\n" \
                   " * @Codery search code\n" \
                   " * @Codery jobs pyhton\n" \
                   " * @Codery jobs java\n" \
                   " * @Codery trending\n" \
                   " * @Codery man execvp\n" \
                   " * @Codery news corona"

    

    codery_keywords = codery_keywords.strip()
    codery_keywords_list=codery_keywords.split(" ")

    if codery_keywords == 'help':
        return help_message

    elif codery_keywords_list[0] == "todo":
        return todo.get_todo_response(codery_keywords,CoderyHandler)

    elif codery_keywords_list[0] == "jobs":
        return jobs.get_jobs(codery_keywords,CoderyHandler)

    elif codery_keywords_list[0] == "leaderboard":
        return leaderboard.get_leaderboard()

    elif codery_keywords_list[0] == "trending":
        return trendingproblems.get_problems()

    elif codery_keywords_list[0] == "search" or codery_keywords_list[0] == "dictionary":
        return dictionary.get_dictionary_response(codery_keywords,CoderyHandler)

    elif codery_keywords_list[0] == "courses" or codery_keywords_list[0] == "course":
        return courses.get_courses(codery_keywords,CoderyHandler)

    elif codery_keywords_list[0] == "jokes" or codery_keywords_list[0] == "joke":
        return geekjokes.get_joke(codery_keywords,CoderyHandler)

    elif codery_keywords_list[0]== "calculator":
        return "The answer is"+calculator.get_calculator_response(codery_keywords,CoderyHandler)

    elif codery_keywords_list[0] == "man":
        
        os.system("man " + codery_keywords_list[1] + " > man.txt")
        file = open("man.txt","r")
        return file.read()

    elif codery_keywords_list[0] == "news":
        return news.get_news_response(codery_keywords,CoderyHandler)

    elif codery_keywords =='contests':
        

        URL = 'https://www.stopstalk.com/contests'


        
        content = requests.get(URL)
        soup = BeautifulSoup(content.text, 'html.parser')
        contentTable  = soup.find('table', { "class" : "centered bordered"}) # Use dictionary to pass key : value pair



        rows  = contentTable.find_all('tr')
        l=[]
        i=0

        for row in rows[1:]:
            l.append("##")
            columns = row.find_all('td')
            for column in columns:
                if column.get_text() != "":
                    l.append((column.get_text()).strip() + "@@")
        
    
            l.append((columns[4].find('a')['href']).strip())
            i+=1
            
        l1="The top contests and hackathons of  today are \n"
        for r in l:
            allContest = r.split("##")
            for eachContest in allContest:
                attrList = eachContest.split("@@")
                for attr in attrList:
                    l1+=attr+"\n"

            

        return l1

    #return a list of top contests
    elif codery_keywords =='top contest':
        URL = 'https://www.stopstalk.com/contests'


        
        content = requests.get(URL)
        soup = BeautifulSoup(content.text, 'html.parser')
        contentTable  = soup.find('table', { "class" : "centered bordered"}) # Use dictionary to pass key : value pair


        
        
        rows  = contentTable.find_all('tr')
        l=[]
        i=0

        for row in rows[1:]:
            l.append("##")
            columns = row.find_all('td')
            for column in columns:
                if column.get_text() != "":
                    l.append((column.get_text()).strip() + "@@")
        
    
            l.append((columns[4].find('a')['href']).strip())
            i+=1
            if i==1:
                break
        l1=""
        for r in l:
            allContest = r.split("##")
            for eachContest in allContest:
                attrList = eachContest.split("@@")
                for attr in attrList:
                    l1+=attr+"\n"

            

        return l1
    
    #to return a list of n top contests
    elif len(codery_keywords_list)==3:

        if codery_keywords_list[0]=="top" and codery_keywords_list[2]=="contests":
            n=int(codery_keywords_list[1])
        else:
            help_message
        URL = 'https://www.stopstalk.com/contests'


        
        content = requests.get(URL)
        soup = BeautifulSoup(content.text, 'html.parser')
        contentTable  = soup.find('table', { "class" : "centered bordered"}) # Use dictionary to pass key : value pair


        
        
        rows  = contentTable.find_all('tr')
        l=[]
        i=0

        for row in rows[1:]:
            l.append("##")
            columns = row.find_all('td')
            for column in columns:
                if column.get_text() != "":
                    l.append((column.get_text()).strip() + "@@")
        
    
            l.append((columns[4].find('a')['href']).strip())
            i+=1
            if i==n:
                break
        l1=""
        for r in l:
            allContest = r.split("##")
            for eachContest in allContest:
                attrList = eachContest.split("@@")
                for attr in attrList:
                    l1+=attr+"\n"

            

        return l1

        

    elif codery_keywords == '' or codery_keywords is None:
        return help_message



        
    
class CoderyHandler(object):
    '''
    This plugin allows users to get the competitive
    coding contests in Zulip. It gets the name, the 
    date, the time left to participate and the links
    to those challenges in zulip and returns it
    to the context (stream or private) in which
    it was called. It gives contests happening on 
    HackerEarth, CodeChef, Codeforces and many other
    competitive programming sites. It looks for 
    messages starting with @codery-bot.
    '''

    def usage(self) -> str:
        return '''
            This plugin will allow users to get the 
            information about competitive coding contests
            and hackathons in Zulip.Use '@codery-bot help' 
            to get more information on the bot usage. Users
            should preface messages with @codery-bot.
            '''

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        original_content = message['content']
        result = get_codery_result(original_content)
        bot_handler.send_reply(message, result)

handler_class = CoderyHandler
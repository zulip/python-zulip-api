from __future__ import absolute_import
from __future__ import print_function
import requests
import logging
import re
from six.moves import urllib

# See readme.md for instructions on running this code.

class WikipediaHandler(object):
    '''
    This plugin facilitates searching Wikipedia for a
    specific key term and returns the top 3 articles from the
    search. It looks for messages starting with '@mention-bot'

    In this example, we write all Wikipedia searches into
    the same stream that it was called from, but this code
    could be adapted to write Wikipedia searches to some
    kind of external issue tracker as well.
    '''

    META = {
        'name': 'Wikipedia',
        'description': 'Searches Wikipedia for a term and returns the top 3 articles.',
    }

    def usage(self):
        return '''
            This plugin will allow users to directly search
            Wikipedia for a specific key term and get the top 3
            articles that is returned from the search. Users
            should preface searches with "@mention-bot".           
            @mention-bot <name of article>'''

    def handle_message(self, message, bot_handler):
        bot_response = self.get_bot_wiki_response(message, bot_handler)
        bot_handler.send_reply(message, bot_response)

    def get_bot_wiki_response(self, message, bot_handler):
        '''This function returns the URLs of the requested topic.'''

        help_text = 'Please enter your search term after @mention-bot'

        #Checking if the link exists. 
        query = message['content']
        if query == '':
            return help_text
        
        query_wiki_link = ('https://en.wikipedia.org/w/api.php?action=query&'
                           'list=search&srsearch=%s&format=json'
                           % (urllib.parse.quote(query),))
        print(query_wiki_link)
        try:
            data = requests.get(query_wiki_link)

        except requests.exceptions.RequestException:
            logging.error('broken link')
            return


        #Checking if the bot accessed the link. 
        if data.status_code != 200:
            logging.error('Page not found.')
            return
        new_content = 'For search term:' + query

        #Checking if there is content for the searched term
        if len(data.json()['query']['search']) == 0:
            new_content = 'I am sorry. The search term you provided is not found :slightly_frowning_face:'
        else:
            search_string1 = data.json()['query']['search'][0]['title'].replace(' ', '_')
            search_string2 = data.json()['query']['search'][1]['title'].replace(' ', '_')
            search_string3 = data.json()['query']['search'][2]['title'].replace(' ', '_')
            url1 = 'https://en.wikipedia.org/wiki/' + search_string1
            url2 = 'https://en.wikipedia.org/wiki/' + search_string2
            url3 = 'https://en.wikipedia.org/wiki/' + search_string3
            new_content = (new_content + '\n'
                           + 'Result 1: ' + url1 + '\n'
                           + 'Result 2: ' + url2 + '\n' 
                           + 'Result 3: ' + url3 + '\n')
        return new_content

    
handler_class = WikipediaHandler

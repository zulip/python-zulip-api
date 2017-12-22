import requests
import logging
import sys

from requests.exceptions import HTTPError, ConnectionError
from typing import Dict, Any, Union, List, Tuple, Optional

commands_list = ('list', 'top', 'help')

class YoutubeHandler(object):

    def usage(self) -> str:
        return '''
            This plugin will allow users to search
            for a given search term on Youtube.
            Use '@mention-bot help' to get more information on the bot usage.
            '''
    help_content = "*Help for YouTube bot* :robot_face: : \n\n" \
                   "The bot responds to messages starting with @mention-bot.\n\n" \
                   "`@mention-bot <search terms>` will return top Youtube video for the given `<search term>`.\n" \
                   "`@mention-bot top <search terms>` also returns the top Youtube result.\n" \
                   "`@mention-bot list <search terms>` will return a list Youtube videos for the given <search term>.\n \n" \
                   "Example:\n" \
                   " * @mention-bot funny cats\n" \
                   " * @mention-bot list funny dogs"

    def initialize(self, bot_handler: Any) -> None:
        self.config_info = bot_handler.get_config_info('youtube')
        # Check if API key is valid. If it is not valid, don't run the bot.
        try:
            search_youtube('test', self.config_info['key'], self.config_info['video_region'])
        except HTTPError as e:
            if (e.response.json()['error']['errors'][0]['reason'] == 'keyInvalid'):
                bot_handler.quit('Invalid key.'
                                 'Follow the instructions in doc.md for setting API key.')
            else:
                raise
        except ConnectionError:
            logging.warning('Bad connection')

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:

        if message['content'] == '' or message['content'] == 'help':
            bot_handler.send_reply(message, self.help_content)
        else:
            cmd, query = get_command_query(message)
            bot_response = get_bot_response(query,
                                            cmd,
                                            self.config_info)
            logging.info(bot_response.format())
            bot_handler.send_reply(message, bot_response)


def search_youtube(query: str, key: str,
                   region: str, max_results: int = 1) -> List[List[str]]:

    videos = []
    params = {
        'part': 'id,snippet',
        'maxResults': max_results,
        'key': key,
        'q': query,
        'alt': 'json',
        'type': 'video',
        'regionCode': region}  # type: Dict[str, Union[str, int]]

    url = 'https://www.googleapis.com/youtube/v3/search'
    try:
        r = requests.get(url, params=params)
    except ConnectionError as e:  # Usually triggered by bad connection.
        logging.exception('Bad connection')
        raise
    r.raise_for_status()
    search_response = r.json()
    # Add each result to the appropriate list, and then display the lists of
    # matching videos, channels, and playlists.
    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            videos.append([search_result['snippet']['title'],
                           search_result['id']['videoId']])
    return videos


def get_command_query(message: Dict[str, str]) -> Tuple[Optional[str], str]:
    blocks = message['content'].lower().split()
    command = blocks[0]
    if command in commands_list:
        query = message['content'][len(command) + 1:].lstrip()
        return command, query
    else:
        return None, message['content']


def get_bot_response(query: Optional[str], command: Optional[str], config_info: Dict[str, str]) -> str:

    key = config_info['key']
    max_results = int(config_info['number_of_results'])
    region = config_info['video_region']
    video_list = []   # type: List[List[str]]
    try:
        if query == '' or query is None:
            return YoutubeHandler.help_content
        if command is None or command == 'top':
            video_list = search_youtube(query, key, region)

        elif command == 'list':
            video_list = search_youtube(query, key, region, max_results)

        elif command == 'help':
            return YoutubeHandler.help_content

    except (ConnectionError, HTTPError):
        return 'Uh-Oh, couldn\'t process the request ' \
               'right now.\nPlease again later'

    reply = 'Here is what I found for `' + query + '` : '

    if len(video_list) == 0:
        return 'Oops ! Sorry I couldn\'t find any video for  `' + query + '` :slightly_frowning_face:'
    elif len(video_list) == 1:
        return (reply + '\n%s - [Watch now](https://www.youtube.com/watch?v=%s)' % (video_list[0][0], video_list[0][1])).strip()

    for title, id in video_list:
        reply = reply + \
            '\n * %s - [Watch now](https://www.youtube.com/watch/%s)' % (title, id)
    # Using link https://www.youtube.com/watch/<id> to
    # prevent showing multiple previews
    return reply


handler_class = YoutubeHandler

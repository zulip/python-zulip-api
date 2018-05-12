import re
import requests
import logging

from typing import Any, Dict

class LinkShortenerHandler(object):
    '''A Zulip bot that will shorten URLs ("links") in a conversation using the
    goo.gl URL shortener.
    '''

    def usage(self) -> str:
        return (
            'Mention the link shortener bot in a conversation and then enter '
            'any URLs you want to shorten in the body of the message. \n\n'
            '`key` must be set in `link_shortener.conf`.')

    def initialize(self, bot_handler: Any) -> None:
        self.config_info = bot_handler.get_config_info('link_shortener')
        self.check_api_key(bot_handler)

    def check_api_key(self, bot_handler: Any) -> None:
        test_request_data = self.call_link_shorten_service('www.youtube.com/watch')  # type: Any
        try:
            if self.is_invalid_token_error(test_request_data):
                bot_handler.quit('Invalid key. Follow the instructions in doc.md for setting API key.')
        except KeyError:
            pass

    def is_invalid_token_error(self, response_json: Any) -> bool:
        return response_json['status_code'] == 500 and response_json['status_txt'] == 'INVALID_ARG_ACCESS_TOKEN'

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        REGEX_STR = (
            '('
            '(?:http|https):\/\/'  # This allows for the HTTP or HTTPS
                                   # protocol.
            '[^"<>\{\}|\\^~[\]` ]+'  # This allows for any character except
                                     # for certain non-URL-safe ones.
            ')'
        )

        HELP_STR = (
            'Mention the link shortener bot in a conversation and '
            'then enter any URLs you want to shorten in the body of '
            'the message.'
        )

        content = message['content']

        if content.strip() == 'help':
            bot_handler.send_reply(
                message,
                HELP_STR
            )
            return

        link_matches = re.findall(REGEX_STR, content)

        shortened_links = [self.shorten_link(link) for link in link_matches]
        link_pairs = [
            (link_match + ': ' + shortened_link)
            for link_match, shortened_link
            in zip(link_matches, shortened_links)
            if shortened_link != ''
        ]
        final_response = '\n'.join(link_pairs)

        if final_response == '':
            bot_handler.send_reply(
                message,
                'No links found. ' + HELP_STR
            )
            return

        bot_handler.send_reply(message, final_response)

    def shorten_link(self, long_url: str) -> str:
        '''Shortens a link using goo.gl Link Shortener and returns it, or
        returns an empty string if something goes wrong.

        Parameters:
            long_url (str): The original URL to shorten.
        '''

        response_json = self.call_link_shorten_service(long_url)
        if response_json['status_code'] == 200 and self.has_shorten_url(response_json):
            shorten_url = self.get_shorten_url(response_json)
        else:
            shorten_url = ''
        return shorten_url

    def call_link_shorten_service(self, long_url: str) -> Any:
        response = requests.get(
            'https://api-ssl.bitly.com/v3/shorten',
            params={'access_token': self.config_info['key'], 'longUrl': long_url}
        )
        return response.json()

    def has_shorten_url(self, response_json: Any) -> bool:
        return 'data' in response_json and 'url' in response_json['data']

    def get_shorten_url(self, response_json: Any) -> str:
        return response_json['data']['url']

handler_class = LinkShortenerHandler

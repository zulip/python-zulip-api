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
        test_request = requests.post(
            'https://www.googleapis.com/urlshortener/v1/url',
            json={'longUrl': 'www.youtube.com/watch'},
            params={'key': self.config_info['key']}
        )  # type: Any
        test_request_data = test_request.json()
        try:
            if test_request_data['error']['errors'][0]['reason'] == 'keyInvalid':
                bot_handler.quit('Invalid key. Follow the instructions in doc.md for setting API key.')
        except KeyError:
            pass

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        REGEX_STR = (
            '('
            '(?:http|https):\/\/'  # This allows for the HTTP or HTTPS
                                   # protocol.
            '[^"<>#%\{\}|\\^~[\]` ]+'  # This allows for any character except
                                       # for certain non-URL-safe ones.
            ')'
        )

        content = message['content']

        if content.strip() == 'help':
            bot_handler.send_reply(
                message,
                (
                    'Mention the link shortener bot in a conversation and '
                    'then enter any URLs you want to shorten in the body of '
                    'the message.'
                )
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
                'No links found. Send "help" to see usage instructions.'
            )
            return

        bot_handler.send_reply(message, final_response)

    def shorten_link(self, long_url: str) -> str:
        '''Shortens a link using goo.gl Link Shortener and returns it, or
        returns an empty string if something goes wrong.

        Parameters:
            long_url (str): The original URL to shorten.
        '''

        body = {'longUrl': long_url}
        params = {'key': self.config_info['key']}

        request = requests.post(
            'https://www.googleapis.com/urlshortener/v1/url',
            json=body,
            params=params
        )

        return request.json().get('id', '')

handler_class = LinkShortenerHandler

# To use this plugin, you need to set up the Google Cloud API key for this bot in
# googletranslate.conf in this (zulip_bots/bots/googletranslate/) directory.

import requests
from requests.exceptions import HTTPError, ConnectionError

class GoogleTranslateHandler(object):
    '''
    This bot will translate any messages sent to it using google translate.
    Before using it, make sure you set up google api keys, and enable google
    cloud translate from the google cloud console.
    '''
    def usage(self):
        return '''
            This plugin allows users translate messages
            Users should @-mention the bot with the format
            @-mention "<text_to_translate>" <target-language> <source-language(optional)>
            '''

    def initialize(self, bot_handler):
        self.config_info = bot_handler.get_config_info('googletranslate')
        # Retrieving the supported languages also serves as a check whether
        # the bot is properly connected to the Google Translate API.
        try:
            self.supported_languages = get_supported_languages(self.config_info['key'])
        except TranslateError as e:
            bot_handler.quit(str(e))

    def handle_message(self, message, bot_handler):
        bot_response = get_translate_bot_response(message['content'],
                                                  self.config_info,
                                                  message['sender_full_name'],
                                                  self.supported_languages)
        bot_handler.send_reply(message, bot_response)

api_url = 'https://translation.googleapis.com/language/translate/v2'

help_text = '''
Google translate bot
Please format your message like:
`@-mention "<text_to_translate>" <target-language> <source-language(optional)>`
Visit [here](https://cloud.google.com/translate/docs/languages) for all languages
'''

language_not_found_text = '{} language not found. Visit [here](https://cloud.google.com/translate/docs/languages) for all languages'

def get_supported_languages(key):
    parameters = {'key': key, 'target': 'en'}
    response = requests.get(api_url + '/languages', params = parameters)
    if response.status_code == requests.codes.ok:
        languages = response.json()['data']['languages']
        return {lang['name'].lower(): lang['language'].lower() for lang in languages}
    raise TranslateError(response.json()['error']['message'])

class TranslateError(Exception):
    pass

def translate(text_to_translate, key, dest, src):
    parameters = {'q': text_to_translate, 'target': dest, 'key': key}
    if src != '':
        parameters.update({'source': src})
    response = requests.post(api_url, params=parameters)
    if response.status_code == requests.codes.ok:
        return response.json()['data']['translations'][0]['translatedText']
    raise TranslateError(response.json()['error']['message'])

def get_code_for_language(language, all_languages):
    if language.lower() not in all_languages.values():
        if language.lower() not in all_languages.keys():
            return ''
        language = all_languages[language.lower()]
    return language

def get_translate_bot_response(message_content, config_file, author, all_languages):
    message_content = message_content.strip()
    if message_content == 'help' or message_content is None or not message_content.startswith('"'):
        return help_text
    split_text = message_content.rsplit('" ', 1)
    if len(split_text) == 1:
        return help_text
    split_text += split_text.pop(1).split(' ')
    if len(split_text) == 2:
        # There is no source language
        split_text.append("")
    if len(split_text) != 3:
        return help_text
    (text_to_translate, target_language, source_language) = split_text
    text_to_translate = text_to_translate[1:]
    target_language = get_code_for_language(target_language, all_languages)
    if target_language == '':
        return language_not_found_text.format("Target")
    if source_language != '':
        source_language = get_code_for_language(source_language, all_languages)
        if source_language == '':
            return language_not_found_text.format("Source")
    try:
        translated_text = translate(text_to_translate, config_file['key'], target_language, source_language)
    except requests.exceptions.ConnectionError as conn_err:
        return "Could not connect to Google Translate. {}.".format(conn_err)
    except TranslateError as tr_err:
        return "Translate Error. {}.".format(tr_err)
    except Exception as err:
        return "Error. {}.".format(err)
    return "{} (from {})".format(translated_text, author)

handler_class = GoogleTranslateHandler

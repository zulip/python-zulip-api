# See readme.md for instructions on running this code.
from __future__ import print_function
import requests
import json

class WeatherHandler(object):
    def initialize(self, bot_handler):
        self.api_key = bot_handler.get_config_info('weather')['key']
        self.response_pattern = 'Weather in {}, {}:\n{:.2f} F / {:.2f} C\n{}'

    def usage(self):
        return '''
            This plugin will give info about weather in a specified city
            '''

    def handle_message(self, message, bot_handler):
        help_content = '''
            This bot returns weather info for specified city.
            You specify city in the following format:
            city, state/country
            state and country parameter is optional(useful when there are many cities with the same name)
            For example:
            @**Weather Bot** Portland
            @**Weather Bot** Portland, Me
            '''.strip()

        if (message['content'] == 'help') or (message['content'] == ''):
            response = help_content
        else:
            url = 'http://api.openweathermap.org/data/2.5/weather?q=' + message['content'] + '&APPID='
            r = requests.get(url + self.api_key)
            if r.json()['cod'] == "404":
                response = "Sorry, city not found"
            else:
                response = format_response(r, message['content'], self.response_pattern)

        bot_handler.send_reply(message, response)


def format_response(text, city, response_pattern):
    j = text.json()
    city = j['name']
    country = j['sys']['country']
    fahrenheit = to_fahrenheit(j['main']['temp'])
    celsius = to_celsius(j['main']['temp'])
    description = j['weather'][0]['description'].title()

    return response_pattern.format(city, country, fahrenheit, celsius, description)


def to_celsius(temp_kelvin):
    return int(temp_kelvin) - 273.15


def to_fahrenheit(temp_kelvin):
    return int(temp_kelvin) * (9. / 5.) - 459.67

handler_class = WeatherHandler

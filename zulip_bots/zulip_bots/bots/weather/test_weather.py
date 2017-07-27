#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from zulip_bots.test_lib import BotTestCase

class TestWeatherBot(BotTestCase):
    bot_name = "weather"

    def test_bot(self):

        # City query
        bot_response = "Weather in New York, US:\n71.33 F / 21.85 C\nMist"
        with self.mock_config_info({'key': '123456'}), \
                self.mock_http_conversation('test_only_city'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': 'New York'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # City with country query
        bot_response = "Weather in New Delhi, IN:\n80.33 F / 26.85 C\nMist"
        with self.mock_config_info({'key': '123456'}), \
                self.mock_http_conversation('test_city_with_country'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': 'New Delhi, India'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # Only country query: returns the weather of the capital city
        bot_response = "Weather in London, GB:\n58.73 F / 14.85 C\nShower Rain"
        with self.mock_config_info({'key': '123456'}), \
                self.mock_http_conversation('test_only_country'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': 'United Kingdom'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )

        # City not found query
        bot_response = "Sorry, city not found"
        with self.mock_config_info({'key': '123456'}), \
                self.mock_http_conversation('test_city_not_found'):
            self.initialize_bot()
            self.assert_bot_response(
                message = {'content': 'fghjklasdfgh'},
                response = {'content': bot_response},
                expected_method='send_reply'
            )
        help_content = '''
            This bot returns weather info for specified city.
            You specify city in the following format:
            city, state/country
            state and country parameter is optional(useful when there are many cities with the same name)
            For example:
            @**Weather Bot** Portland
            @**Weather Bot** Portland, Me
            '''.strip()

        # help message
        bot_response = help_content
        self.assert_bot_response(
            message = {'content': 'help'},
            response = {'content': bot_response},
            expected_method='send_reply'
        )

        # empty message
        bot_response = help_content
        self.assert_bot_response(
            message = {'content': ''},
            response = {'content': bot_response},
            expected_method='send_reply'
        )

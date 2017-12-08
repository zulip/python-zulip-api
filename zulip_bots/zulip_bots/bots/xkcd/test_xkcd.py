#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import mock
from mock import MagicMock, patch
from zulip_bots.test_lib import BotTestCase

class TestXkcdBot(BotTestCase):
    bot_name = "xkcd"

    def test_latest_command(self):
        bot_response = ("#1866: **Russell's Teapot**\n"
                        "[Unfortunately, NASA regulations state that Bertrand Russell-related "
                        "payloads can only be launched within launch vehicles which do not launch "
                        "themselves.](https://imgs.xkcd.com/comics/russells_teapot.png)")
        with self.mock_http_conversation('test_latest'):
            self.verify_reply('latest', bot_response)

    def test_random_command(self):
        bot_response = ("#1800: **Chess Notation**\n"
                        "[I've decided to score all my conversations using chess win-loss "
                        "notation. (??)](https://imgs.xkcd.com/comics/chess_notation.png)")
        with self.mock_http_conversation('test_random'):
            # Mock randint function.
            with patch('zulip_bots.bots.xkcd.xkcd.random.randint') as randint:
                mock_rand_value = mock.MagicMock()
                mock_rand_value.return_value = 1800
                randint.return_value = mock_rand_value.return_value
                self.verify_reply('random', bot_response)

    def test_numeric_comic_id_command_1(self):
        bot_response = ("#1: **Barrel - Part 1**\n[Don't we all.]"
                        "(https://imgs.xkcd.com/comics/barrel_cropped_(1).jpg)")
        with self.mock_http_conversation('test_specific_id'):
            self.verify_reply('1', bot_response)

    @mock.patch('logging.exception')
    def test_invalid_comic_ids(self, mock_logging_exception):
        invalid_id_txt = "Sorry, there is likely no xkcd comic strip with id: #"

        bot_response = invalid_id_txt + "999999999"
        with self.mock_http_conversation('test_not_existing_id'):
            self.verify_reply('999999999', bot_response)

        bot_response = invalid_id_txt + "0"
        with self.mock_http_conversation('test_not_existing_id_2'):
            self.verify_reply('0', bot_response)

    def test_help_responses(self):
        help_txt = "xkcd bot supports these commands:"
        err_txt  = "xkcd bot only supports these commands, not `{}`:"
        commands = '''
* `@xkcd help` to show this help message.
* `@xkcd latest` to fetch the latest comic strip from xkcd.
* `@xkcd random` to fetch a random comic strip from xkcd.
* `@xkcd <comic id>` to fetch a comic strip based on `<comic id>` e.g `@xkcd 1234`.'''
        # Empty query, no request made to the Internet.
        bot_response = err_txt.format('')+commands
        self.verify_reply('', bot_response)

        # 'help' command.
        bot_response = help_txt+commands
        self.verify_reply('help', bot_response)

        # wrong command.
        bot_response = err_txt.format('x')+commands
        self.verify_reply('x', bot_response)

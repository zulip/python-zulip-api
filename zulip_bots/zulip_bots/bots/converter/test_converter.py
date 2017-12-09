#!/usr/bin/env python

from zulip_bots.test_lib import StubBotTestCase

class TestConverterBot(StubBotTestCase):
    bot_name = "converter"

    def test_bot(self):
        dialog = [
            ("", 'Too few arguments given. Enter `@convert help` '
                 'for help on using the converter.\n'),
            ("foo bar", 'Too few arguments given. Enter `@convert help` '
                        'for help on using the converter.\n'),
            ("2 m cm", "2.0 m = 200.0 cm\n"),
            ("12.0 celsius fahrenheit", "12.0 celsius = 53.600054 fahrenheit\n"),
            ("0.002 kilometer millimile", "0.002 kilometer = 1.2427424 millimile\n"),
            ("3 megabyte kilobit", "3.0 megabyte = 24576.0 kilobit\n"),
        ]
        self.verify_dialog(dialog)

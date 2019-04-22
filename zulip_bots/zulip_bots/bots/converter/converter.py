# See readme.md for instructions on running this code.

import copy
import importlib
from math import log10, floor

import re
from zulip_bots.bots.converter import utils

from typing import Any, Dict, List, Tuple


def is_float(value: Any) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False

# Rounds the number 'x' to 'digits' significant digits.
# A normal 'round()' would round the number to an absolute amount of
# fractional decimals, e.g. 0.00045 would become 0.0.
# 'round_to()' rounds only the digits that are not 0.
# 0.00045 would then become 0.0005.


def round_to(x: float, digits: int) -> float:
    return round(x, digits-int(floor(log10(abs(x)))))


class ConverterHandler(object):
    '''
    This plugin allows users to make conversions between various units,
    e.g. Celsius to Fahrenheit, or kilobytes to gigabytes.
    It looks for messages of the format
    '@mention-bot <number> <unit_from> <unit_to>'
    The message '@mention-bot help' posts a short description of how to use
    the plugin, along with a list of all supported units.
    '''

    def usage(self) -> str:
        return '''
               This plugin allows users to make conversions between
               various units, e.g. Celsius to Fahrenheit,
               or kilobytes to gigabytes. It looks for messages of
               the format '@mention-bot <number> <unit_from> <unit_to>'
               The message '@mention-bot help' posts a short description of
               how to use the plugin, along with a list of
               all supported units.
               '''

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        bot_response = get_bot_converter_response(message, bot_handler)
        bot_handler.send_reply(message, bot_response)


class UnitHandler(object):
    '''This class handles the units that were input by the user.'''

    def __init__(self, words: List[Any], convert_index: int) -> None:
        '''Retrieve proper units from utils, convert any abbreviations to full.'''
        unit_from_raw = words[convert_index + 2]
        unit_to_raw = words[convert_index + 3]

        self.unit_from = utils.ALIASES.get(unit_from_raw, unit_from_raw)
        self.unit_to = utils.ALIASES.get(unit_to_raw, unit_to_raw)

    @property
    def fr(self) -> str:
        '''Getter for the input unit'''
        return self.unit_from

    @property
    def to(self) -> str:
        '''Getter for the output unit'''
        return self.unit_to

    def make_exponent(self, exponent: int) -> int:
        '''Create proper exponent for conversion, chop off prefix to units.'''
        for key, exp in utils.PREFIXES.items():
            if self.unit_from.startswith(key):
                exponent += exp
                self.unit_from = self.unit_from[len(key):]
            if self.unit_to.startswith(key):
                exponent -= exp
                self.unit_to = self.unit_to[len(key):]

        return exponent

    def check(self, uf_to_std: List[Any], ut_to_std: List[Any], results: List[Any]) -> bool:
        '''Return if the units are valid, also handles Kelvin units.'''
        if not uf_to_std:
            results.append('`' + self.unit_from +
                           '` is not a valid unit. ' + utils.QUICK_HELP)
        else:
            if uf_to_std[2] == 'kelvin':
                self.unit_from = self.unit_from.capitalize()
        if not ut_to_std:
            results.append('`' + self.unit_to +
                           '` is not a valid unit.' + utils.QUICK_HELP)
        if not uf_to_std or not ut_to_std:
            return False
        if uf_to_std[2] != ut_to_std[2]:
            results.append('`' + self.unit_to.capitalize() + '` and `' + self.unit_from + '`' +
                           ' are not from the same category. ' + utils.QUICK_HELP)
            return False

        return True


def get_bot_converter_response(message: Dict[str, str], bot_handler: Any) -> str:
    content = message['content']

    words = content.lower().split()
    convert_indexes = [i for i, word in enumerate(words) if word == "@convert"]
    convert_indexes = [-1] + convert_indexes
    results = []

    for convert_index in convert_indexes:
        if (convert_index + 1) < len(words) and words[convert_index + 1] == 'help':
            results.append(utils.HELP_MESSAGE)
            continue

        if (convert_index + 3) >= len(words):
            results.append('Too few arguments given. ' + utils.QUICK_HELP)
            continue

        number = words[convert_index + 1]
        exponent = 0

        units = UnitHandler(words, convert_index)

        if not is_float(number):
            results.append(
                '`' + number + '` is not a valid number. ' + utils.QUICK_HELP)
            continue

        # cannot reassign "number" as a float after using as string, so changed name
        convert_num = float(number)
        number_res = copy.copy(convert_num)

        exponent = units.make_exponent(exponent)
        uf_to_std = utils.UNITS.get(units.fr, [])  # type: List[Any]
        ut_to_std = utils.UNITS.get(units.to, [])  # type: List[Any]

        if not units.check(uf_to_std, ut_to_std, results):
            continue

        base_unit = uf_to_std[2]

        # perform the conversion between the units
        number_res *= uf_to_std[1]
        number_res += uf_to_std[0]
        number_res -= ut_to_std[0]
        number_res /= ut_to_std[1]

        if base_unit == 'bit':
            number_res *= 1024 ** (exponent // 3)
        else:
            number_res *= 10 ** exponent
        number_res = round_to(number_res, 7)

        results.append('{} {} = {} {}'.format(number,
                                              words[convert_index + 2],
                                              number_res,
                                              words[convert_index + 3]))

    new_content = ''
    for idx, result in enumerate(results, 1):
        new_content += ((str(idx) + '. conversion: ')
                        if len(results) > 1 else '') + result + '\n'

    return new_content


handler_class = ConverterHandler

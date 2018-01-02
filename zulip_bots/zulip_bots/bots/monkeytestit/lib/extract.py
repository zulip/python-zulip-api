"""This module fetches the report from the website by doing a get request to
the predefined url. The result is then parsed to JSON for further management
in report.py
"""

import json

import requests


def fetch(options: dict):
    """Makes a request then returns the dictionary version of the response

    :param options: Options dictionary containing the payload for the request
    :return: A dictionary containing keys and values to be managed by report.py
    :raises JSONDecodeError: if the get is unsuccessful. This could mean
            faulty link or any other causes.
    """

    res = requests.get("https://monkeytest.it/test", params=options)

    if "server timed out" in res.text:
        return {"error": "The server timed out before sending a response to "
                         "the request. Report is available at "
                         "[Test Report History]"
                         "(https://monkeytest.it/dashboard)."}

    return json.loads(res.text)

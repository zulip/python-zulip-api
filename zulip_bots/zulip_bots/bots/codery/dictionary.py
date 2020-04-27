from PyDictionary import PyDictionary
from typing import Any
from typing import Dict


def get_dictionary_response(content, bot_handler: Any) -> str:

    words = content.lower().split()
    dictionary = PyDictionary()
    res = dictionary.meaning(words[1])
    if res != None:
        res = res['Noun']
        ans = ""
        for i in res:
            ans = ans + i + "\n\n"
        return ans
    return "Unable to find meaning :("

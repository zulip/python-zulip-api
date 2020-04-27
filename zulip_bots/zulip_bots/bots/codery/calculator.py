import sys
import os
sys.path.insert(0, os.getcwd())
from typing import Any


def get_calculator_response(content, bot_handler: Any) -> str:
    words = content.lower().split()
    print(words)
    if words[2] == "+":
        temp = float(words[1])
        temp1 = float(words[3])
        temp = temp + temp1
        return str(temp)
    elif words[2] == "-":
        temp = float(words[1])
        temp1 = float(words[3])
        temp = temp - temp1
        return str(temp)
    elif words[2] == "*":
        temp = float(words[1])
        temp1 = float(words[3])
        temp = temp * temp1
        return str(temp)
    elif words[2] == "/":
        if words[3] == "0":
            return "Division by zero."
        temp = float(words[1])
        temp1 = float(words[3])
        temp = temp / temp1
        return str(temp)
    else:
        return "Please apply spaces after each number of mathematical operator"

from itertools import cycle

# Terminal Color codes for use in differentiatng linters
BOLDRED = "\x1B[1;31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
CYAN = "\x1b[36m"
ENDC = "\033[0m"

colors = cycle([GREEN, YELLOW, BLUE, MAGENTA, CYAN])


def print_err(name: str, color: str, line: str) -> None:
    print(
        "{color}{name}{pad}|{end} {red_color}{line!s}{end}".format(
            color=color,
            name=name,
            pad=" " * max(0, 10 - len(name)),
            red_color=BOLDRED,
            line=line.rstrip(),
            end=ENDC,
        ),
        flush=True,
    )

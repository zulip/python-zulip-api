import signal
import subprocess
from typing import Callable, Sequence

from zulint.printer import print_err


def run_command(
    name: str,
    color: str,
    command: Sequence[str],
    suppress_line: Callable[[str], bool] = lambda line: False,
) -> int:
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    ) as p:
        assert p.stdout is not None
        for line in iter(p.stdout.readline, ""):
            if not suppress_line(line):
                print_err(name, color, line)
        if p.wait() < 0:
            try:
                signal_name = signal.Signals(-p.returncode).name
            except (AttributeError, ValueError):
                signal_name = f"signal {-p.returncode}"
            print_err(name, color, f"{command[0]} terminated by {signal_name}")
        return p.returncode

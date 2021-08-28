from typing import Set, Tuple

import _zephyr
from _zephyr import ZNotice as ZNotice
from _zephyr import receive as receive

_z = _zephyr
__inited: bool

def init() -> None: ...

class Subscriptions(Set[Tuple[str, str, str]]):
    pass

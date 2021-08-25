import pkgutil
from typing import Iterable

__path__ = pkgutil.extend_path(__path__, __name__)  # type: Iterable[str]

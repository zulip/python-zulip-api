import pkgutil
from typing import List

__path__ = pkgutil.extend_path(__path__, __name__)  # type: List[str]

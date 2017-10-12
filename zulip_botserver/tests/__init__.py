import pkgutil
from typing import Iterable, Text

__path__ = pkgutil.extend_path(__path__, __name__)  # type: Iterable[Text]

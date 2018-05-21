import sys
from os.path import basename, splitext
from typing import Any, Optional, Text

def import_module_from_source(path: Text, name: Optional[Text]=None) -> Any:
    if not name:
        name = splitext(basename(path))[0]

    # importlib.util.module_from_spec is supported from Python3.5
    py_version = sys.version_info
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 5):
        import imp
        module = imp.load_source(name, path)
    else:
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        loader = spec.loader
        if loader is None:
            return None
        loader.exec_module(module)

    return module

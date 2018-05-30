import sys
import os
from os.path import basename, splitext
from typing import Any, Optional, Text, Tuple

current_dir = os.path.dirname(os.path.abspath(__file__))

def import_module_from_source(path: Text, name: Text) -> Any:

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

def import_module_by_name(name: Text) -> Any:
    import importlib
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        return None

def resolve_bot_path(name: Text) -> Optional[Tuple[Text, Text]]:
    if os.path.isfile(name):
        bot_path = os.path.abspath(name)
        bot_name = splitext(basename(bot_path))[0]
        return (bot_path, bot_name)
    else:
        bot_name = name
        bot_path = os.path.abspath(os.path.join(current_dir, 'bots', bot_name, bot_name + '.py'))
        if os.path.isfile(bot_path):
            return (bot_path, bot_name)

    return None

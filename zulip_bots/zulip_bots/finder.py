import importlib
import importlib.abc
import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import Any, Optional, Tuple

current_dir = os.path.dirname(os.path.abspath(__file__))

import importlib_metadata as metadata


def import_module_from_source(path: str, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None:
        return None
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if not isinstance(loader, importlib.abc.Loader):
        return None
    loader.exec_module(module)
    return module


def import_module_by_name(name: str) -> Any:
    try:
        return importlib.import_module(name)
    except ImportError:
        return None


class DuplicateRegisteredBotNameError(Exception):
    pass


def import_module_from_zulip_bot_registry(name: str) -> Tuple[str, Optional[ModuleType]]:
    # Prior to Python 3.10, calling importlib.metadata.entry_points returns a
    # SelectableGroups object when no parameters is given. Currently we use
    # the importlib_metadata library for compatibility, but we need to migrate
    # to the built-in library when we start to adapt Python 3.10.
    # https://importlib-metadata.readthedocs.io/en/latest/using.html#entry-points
    registered_bots = metadata.entry_points(group="zulip_bots.registry")
    matching_bots = [bot for bot in registered_bots if bot.name == name]

    if len(matching_bots) == 1:  # Unique matching entrypoint
        """We expect external bots to be registered using entry_points in the
        group "zulip_bots.registry", where the name of the entry point should
        match the name of the module containing the bot handler and the value
        of it should be the package containing the bot handler module.

        E.g, an Python package for a bot called "packaged_bot" should have an
        `entry_points` setup like the following:

        setup(
            ...
            entry_points={
                "zulip_bots.registry":[
                    "packaged_bot=packaged_bot.packaged_bot"
                ]
            }
            ...
        )
        """
        bot = matching_bots[0]
        bot_name = bot.name
        bot_module = bot.load()
        bot_version = bot_module.__version__

        if bot_version is not None:
            return f"{bot_name}: {bot_version}", bot_module
        else:
            return f"editable package: {bot_name}", bot_module

    if len(matching_bots) > 1:
        raise DuplicateRegisteredBotNameError(name)

    return "", None  # no matches in registry


def resolve_bot_path(name: str) -> Optional[Tuple[Path, str]]:
    if os.path.isfile(name):
        bot_path = Path(name)
        bot_name = Path(bot_path).stem
        return (bot_path, bot_name)
    else:
        bot_name = name
        bot_path = Path(current_dir, "bots", bot_name, bot_name + ".py")
        if os.path.isfile(bot_path):
            return (bot_path, bot_name)

    return None

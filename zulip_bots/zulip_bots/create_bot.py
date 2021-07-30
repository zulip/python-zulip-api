import argparse
import os
from pathlib import Path

DOC_TEMPLATE = """Simple Zulip bot that will respond to any query with a "beep boop".

This is a boilerplate bot that can be used as a template for more
sophisticated/evolved Zulip bots that can be installed separately.
"""


README_TEMPLATE = """This is a boilerplate package for a Zulip bot that can be installed from pip
and launched using the `zulip-run-bots` command.
"""

SETUP_TEMPLATE = """import {bot_name}
from setuptools import find_packages, setup

package_info = {{
    "name": "{bot_name}",
    "version": {bot_name}.__version__,
    "entry_points": {{
        "zulip_bots.registry": ["{bot_name}={bot_name}.{bot_name}"],
    }},
    "packages": find_packages(),
}}

setup(**package_info)
"""

BOT_MODULE_TEMPLATE = """# See readme.md for instructions on running this code.
from typing import Any, Dict

import {bot_name}

from zulip_bots.lib import BotHandler

__version__ = {bot_name}.__version__


class {handler_name}:
    def usage(self) -> str:
        return \"""
        This is a boilerplate bot that responds to a user query with
        "beep boop", which is robot for "Hello World".

        This bot can be used as a template for other, more
        sophisticated, bots that can be installed separately.
        \"""

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        content = "beep boop"  # type: str
        bot_handler.send_reply(message, content)

        emoji_name = "wave"  # type: str
        bot_handler.react(message, emoji_name)


handler_class = {handler_name}
"""


def create_bot_file(path: Path, file_name: str, content: str) -> None:
    with open(Path(path, file_name), "w") as file:
        file.write(content)


def parse_args() -> argparse.Namespace:
    usage = """
        zulip-create-bot <bot_name>
        zulip-create-bot --help
        """

    parser = argparse.ArgumentParser(usage=usage, description="Create a minimal Zulip bot package.")

    parser.add_argument("bot", help="the name of the bot to be created")

    parser.add_argument("--output", "-o", help="the target directory for the new bot", default=".")

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="forcibly overwrite the existing files in the output directory",
    )

    parser.add_argument("--quiet", "-q", action="store_true", help="turn off logging output")

    args = parser.parse_args()

    if not args.bot.isidentifier():
        parser.error(f'"{args.bot}" is not a valid Python identifier')

    if args.output is not None and not os.path.isdir(args.output):
        parser.error(f"{args.output} is not a valid path")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    handler_name = f'{args.bot.title().replace("_", "")}Handler'

    bot_path = Path(args.output, args.bot)
    bot_module_path = Path(bot_path, args.bot)

    try:
        os.mkdir(bot_path)
        os.mkdir(bot_module_path)
    except FileExistsError as err:
        if not args.force:
            print(
                f'The directory "{err.filename}" already exists\nUse -f or --force to forcibly overwrite the existing files'
            )
            exit(1)

    create_bot_file(bot_path, "README.md", README_TEMPLATE)
    create_bot_file(bot_path, "setup.py", SETUP_TEMPLATE.format(bot_name=args.bot))
    create_bot_file(bot_module_path, "doc.md", DOC_TEMPLATE.format(bot_name=args.bot))
    create_bot_file(bot_module_path, "__init__.py", '__version__ = "1.0.0"')
    create_bot_file(
        bot_module_path,
        f"{args.bot}.py",
        BOT_MODULE_TEMPLATE.format(bot_name=args.bot, handler_name=handler_name),
    )

    output_path = os.path.abspath(bot_path)
    if not args.quiet:
        print(
            f"""Successfully set up {args.bot} at {output_path}\n
        You can install it with "pip install -e {output_path}"\n
        and then run it with "zulip-run-bot -r {args.bot} -c CONFIG_FILE"
        """
        )


if __name__ == "__main__":
    main()

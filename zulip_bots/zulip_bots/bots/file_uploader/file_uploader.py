import os
from pathlib import Path
from typing import Dict

from zulip_bots.lib import BotHandler


class FileUploaderHandler:
    def usage(self) -> str:
        return (
            "This interactive bot is used to upload files (such as images) to the Zulip server:"
            "\n- @uploader <local_file_path> : Upload a file, where <local_file_path> is the path to the file"
            "\n- @uploader help : Display help message"
        )

    def handle_message(self, message: Dict[str, str], bot_handler: BotHandler) -> None:
        help_str = (
            "Use this bot with any of the following commands:"
            "\n* `@uploader <local_file_path>` : Upload a file, where `<local_file_path>` is the path to the file"
            "\n* `@uploader help` : Display help message"
        )

        content = message["content"].strip()
        if content == "help":
            bot_handler.send_reply(message, help_str)
            return

        path = Path(os.path.expanduser(content))
        if not path.is_file():
            bot_handler.send_reply(message, f"File `{content}` not found")
            return

        path = path.resolve()
        upload = bot_handler.upload_file_from_path(str(path))
        if upload["result"] != "success":
            msg = upload["msg"]
            bot_handler.send_reply(message, f"Failed to upload `{path}` file: {msg}")
            return

        uploaded_file_reply = "[{}]({})".format(path.name, upload["uri"])
        bot_handler.send_reply(message, uploaded_file_reply)


handler_class = FileUploaderHandler

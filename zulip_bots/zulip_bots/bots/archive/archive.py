"""
Note: this bot was written by Kimi K2.
"""

import re

import waybackpy


class ArchiveBotHandler:
    def usage(self) -> str:
        return """
        This bot listens for messages containing URLs, saves each URL to the
        Internet Archive, and replies with the fresh archive.org link(s).
        Mention the bot or send it a PM that contains a URL.
        """

    def handle_message(self, message: dict, bot_handler) -> None:
        content = message["content"]
        urls = re.findall(r"https?://[^\s]+", content)
        if not urls:
            return

        replies = []
        for url in urls:
            try:
                archive_url = waybackpy.Url(url).save()
                replies.append(f"Archived: {archive_url}")
            except Exception as exc:
                replies.append(f"Failed to archive {url} – {exc}")

        if replies:
            bot_handler.send_reply(message, "\n".join(replies))


handler_class = ArchiveBotHandler

import re
from typing import Match

CODE_REGEX = re.compile(r"(```[\s\S]*?```|`[^`\n]+`)")


def _slack_user_repl(match: Match[str]) -> str:
    return f"@**{match.group(2) or match.group(1)}**"


def _slack_channel_repl(match: Match[str]) -> str:
    return f"#**{match.group(2) or match.group(1)}**"


def zulip_to_slack_markdown(text: str) -> str:
    """Translate Zulip GFM markdown to Slack mrkdwn syntax.

    Preserves code blocks and inline code spans without modification.
    """
    parts = CODE_REGEX.split(text)
    for i in range(0, len(parts), 2):
        s = parts[i]
        # Wildcard mentions
        s = re.sub(r"@\*\*(all|everyone)\*\*", r"<!everyone>", s)
        s = re.sub(r"@\*\*(channel|stream)\*\*", r"<!channel>", s)
        s = re.sub(r"@\*\*here\*\*", r"<!here>", s)
        # User mentions: @**Name**, @**Name|1234**, @_**Name**
        s = re.sub(r"@_?\*\*([^*]+?)(?:\|\d+)?\*\*", r"<@\1>", s)
        # Stream links: #**stream** or #**stream>topic**
        s = re.sub(r"#\*\*([^*>]+)(?:>[^*]+)?\*\*", r"#\1", s)
        # Markdown links: [label](url) -> <url|label>
        s = re.sub(r"\[([^\]\n]+)\]\(([^)\s]+)\)", r"<\2|\1>", s)
        # Simple @username mentions
        s = re.sub(r"(^|\s)@([a-zA-Z0-9_\-\.]+)(?=\s|$|[.,!?])", r"\1<@\2>", s)
        # Italic: *text* -> _text_ (when not part of **)
        s = re.sub(r"(?<!\*)\*([^\*\s\n](?:.*?[^\*\s\n])?)\*(?!\*)", r"_\1_", s)
        # Bold: **text** -> *text*
        s = re.sub(r"\*\*([^\*\n]+?)\*\*", r"*\1*", s)
        # Strikethrough: ~~text~~ -> ~text~
        s = re.sub(r"~~([^~\n]+?)~~", r"~\1~", s)
        parts[i] = s
    return "".join(parts)


def slack_to_zulip_markdown(text: str) -> str:
    """Translate Slack mrkdwn syntax to Zulip GFM markdown.

    Preserves code blocks and inline code spans without modification.
    """
    parts = CODE_REGEX.split(text)
    for i in range(0, len(parts), 2):
        s = parts[i]
        # Wildcard mentions
        s = re.sub(r"<!everyone>", r"@**everyone**", s)
        s = re.sub(r"<!channel>", r"@**channel**", s)
        s = re.sub(r"<!here>", r"@**here**", s)
        # Channel mentions: <#C123|channel> -> #**channel**, <#C123> -> #**C123**
        s = re.sub(r"<#([a-zA-Z0-9_\-\.]+)(?:\|([^>]+))?>", _slack_channel_repl, s)
        # User mentions: <@U123|user> -> @**user**, <@U123> -> @**U123**
        s = re.sub(r"<@([a-zA-Z0-9_\-\.]+)(?:\|([^>]+))?>", _slack_user_repl, s)
        # Links with label: <url|label> -> [label](url)
        s = re.sub(r"<([^|>]+)\|([^>]+)>", r"[\2](\1)", s)
        # Bare URLs: <url> -> url
        s = re.sub(r"<((?:https?|mailto):[^>|]+)>", r"\1", s)
        # Bold: *text* -> **text**
        s = re.sub(
            r"(^|[\s.,!?;:\(])\*([^\*\s\n](?:.*?[^\*\s\n])?)\*(?=[\s.,!?;:\)]|$)",
            r"\1**\2**",
            s,
        )
        # Strikethrough: ~text~ -> ~~text~~
        s = re.sub(
            r"(^|[\s.,!?;:\(])~([^~\s\n](?:.*?[^~\s\n])?)~(?=[\s.,!?;:\)]|$)",
            r"\1~~\2~~",
            s,
        )
        parts[i] = s
    return "".join(parts)

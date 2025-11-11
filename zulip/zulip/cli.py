#!/usr/bin/env python3
import logging
import sys
from typing import Any, Dict, List

import click
import zulip

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger("zulip-cli")

client = zulip.Client(config_file="~/zuliprc")


@click.group()
def cli() -> None:
    pass


def exit_on_result(result: str) -> None:
    if result == "success":
        sys.exit(0)
    sys.exit(1)


def log_exit(response: Dict[str, Any]) -> None:
    result = response["result"]
    if result == "success":
        log.info(response)
    else:
        log.error(response)
    exit_on_result(result)


# Messages API


@cli.command()
@click.argument("recipients", type=str, nargs=-1)
@click.option(
    "--stream",
    "-s",
    default="",
    help="Allows the user to specify a stream for the message.",
)
@click.option(
    "--subject",
    "-S",
    default="",
    help="Allows the user to specify a subject for the message.",
)
@click.option("--message", "-m", required=True)
@click.option(
    "--type",
    "-t",
    "message_type",
    default="private",
    help="Message type: 'stream', 'private', or 'direct'.",
)
def send_message(
    recipients: List[str], stream: str, subject: str, message: str, message_type: str
) -> None:
    """Sends a message and optionally prints status about the same."""

    # Sanity check user data
    has_stream = stream != ""
    has_subject = subject != ""
    if len(recipients) != 0 and has_stream:
        click.echo("You cannot specify both a username and a stream/subject.")
        raise SystemExit(1)
    if len(recipients) == 0 and has_stream != has_subject:
        click.echo("Stream messages must have a subject.")
        raise SystemExit(1)
    if len(recipients) == 0 and not has_stream:
        click.echo("You must specify a stream/subject or at least one recipient.")
        raise SystemExit(1)

    # Normalize message type
    if message_type not in ("stream", "private", "direct"):
        click.echo("Invalid message type. Use 'stream', 'private', or 'direct'.")
        raise SystemExit(1)

    # Determine type
    if has_stream:
        message_data: Dict[str, Any] = {
            "type": "stream",
            "content": message,
            "subject": subject,
            "to": stream,
        }
    else:
        # Default to "direct" if explicitly given, else private
        message_data = {
            "type": "direct" if message_type == "direct" else "private",
            "content": message,
            "to": recipients,
        }

    # Backward compatibility: convert "direct" → "private" if server doesn’t support feature level 174+
    if message_data["type"] == "direct":
        try:
            if client.server_feature_level() < 174:
                log.info(
                    "Server does not support 'direct' message type; falling back to 'private'."
                )
                message_data["type"] = "private"
        except Exception:
            # Fallback: assume older server
            message_data["type"] = "private"

    if message_data["type"] == "stream":
        log.info(
            "Sending message to stream %r, subject %r... ",
            message_data["to"],
            message_data["subject"],
        )
    else:
        log.info("Sending %r message to %s... ", message_data["type"], message_data["to"])

    response = client.send_message(message_data)
    log_exit(response)


@cli.command()
def upload_file() -> None:
    """Upload a single file and get the corresponding URI."""
    # TODO


@cli.command()
@click.argument("message_id", type=int)
@click.option("--message", "-m", required=True)
def update_message(message_id: int, message: str) -> None:
    """Edit/update the content or topic of a message."""
    request = {
        "message_id": message_id,
        "content": message,
    }
    response = client.update_message(request)
    log_exit(response)


@cli.command()
@click.argument("message_id", type=int)
def delete_message(message_id: int) -> None:
    """Permanently delete a message."""
    response = client.delete_message(message_id)
    log_exit(response)


@cli.command()
@click.argument("message_id", type=int)
@click.argument("emoji_name")
def add_reaction(message_id: int, emoji_name: str) -> None:
    """Add an emoji reaction to a message."""
    request = {
        "message_id": message_id,
        "emoji_name": emoji_name,
    }

    response = client.add_reaction(request)
    log_exit(response)


@cli.command()
@click.argument("message_id", type=int)
@click.argument("emoji_name")
def remove_reaction(message_id: int, emoji_name: str) -> None:
    """Remove an emoji reaction from a message."""
    request = {
        "message_id": message_id,
        "emoji_name": emoji_name,
    }

    response = client.remove_reaction(request)
    log_exit(response)


@cli.command()
@click.argument("message_id", type=int)
def get_message_history(message_id: int) -> None:
    """Fetch the message edit history of a previously edited message."""
    response = client.get_message_history(message_id)
    log_exit(response)


@cli.command()
def mark_all_as_read() -> None:
    """Marks all of the current user's unread messages as read."""
    response = client.mark_all_as_read()
    log_exit(response)


@cli.command()
def get_subscriptions() -> None:
    """Get all streams that the user is subscribed to."""
    response = client.get_subscriptions()
    log_exit(response)


if __name__ == "__main__":
    cli()

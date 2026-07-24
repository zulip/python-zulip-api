#!/usr/bin/env python3
#
# A ClickUp integration script for Zulip.

import argparse
import json
import sys
from typing import Any, Optional, Union
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

EVENT_CHOICES: dict[str, tuple[str, ...]] = {
    "task": ("taskCreated", "taskUpdated", "taskDeleted"),
    "list": ("listCreated", "listUpdated", "listDeleted"),
    "folder": ("folderCreated", "folderUpdated", "folderDeleted"),
    "space": ("spaceCreated", "spaceUpdated", "spaceDeleted"),
    "goal": ("goalCreated", "goalUpdated", "goalDeleted"),
    "target": ("keyResultCreated", "keyResultUpdated", "keyResultDeleted"),
}


def get_event_choices_string() -> str:
    choices_string = ""
    for index, key in enumerate(EVENT_CHOICES):
        choices_string += f"    {index + 1} = {key}\n"
    return choices_string


class ClickUpAPIHandler:
    def __init__(
        self,
        api_key: str,
        team_id: str,
    ) -> None:
        self.api_key: str = api_key
        self.team_id: str = team_id
        self.ENDPOINTS: dict[str, str] = {
            "team": f"team/{self.team_id}/webhook",
            "webhook": "webhook/{webhook_id}",
        }

    def make_clickup_request(
        self, endpoint: str, query: dict[str, Union[str, list[str]]], method: str
    ) -> Optional[dict[str, Any]]:
        base_url = "https://api.clickup.com/api/v2/"
        api_endpoint = urljoin(base_url, endpoint)

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": self.api_key,
        }
        body = json.dumps(query).encode("utf-8") if query else None
        req = Request(api_endpoint, data=body, headers=headers, method=method)  # noqa: S310

        try:
            with urlopen(req) as response:  # noqa: S310
                raw = response.read().decode("utf-8")
                data: dict[str, Any] = json.loads(raw)
                return data
        except HTTPError as err:
            print(f"HTTPError occurred: {err.code} {err.reason}")
            return None
        except URLError as err:
            print(f"Network error occurred: {err.reason}")
            return None
        except ValueError as err:
            print(f"Could not parse ClickUp's response: {err}")
            return None

    def create_webhook(self, end_point: str, events: list[str]) -> dict[str, Any]:
        # https://clickup.com/api/clickupreference/operation/CreateWebhook/
        query: dict[str, Union[str, list[str]]] = {
            "endpoint": end_point,
            "events": events,
        }

        if (data := self.make_clickup_request(self.ENDPOINTS["team"], query, "POST")) is None:
            print("We're unable to create webhook at the moment.")
            sys.exit(1)
        return data

    def get_webhooks(self) -> dict[str, Any]:
        # https://clickup.com/api/clickupreference/operation/GetWebhooks/
        if (data := self.make_clickup_request(self.ENDPOINTS["team"], {}, "GET")) is None:
            print("We're unable to fetch webhooks at the moment.")
            sys.exit(1)
        return data

    def delete_webhook(self, webhook_id: str) -> None:
        # https://clickup.com/api/clickupreference/operation/DeleteWebhook/
        endpoint = self.ENDPOINTS["webhook"].format(webhook_id=webhook_id)
        if self.make_clickup_request(endpoint, {}, "DELETE") is None:
            print("Failed to delete webhook.")
            sys.exit(1)
        else:
            print(f"Webhook ID: {webhook_id} has been deleted.")


def query_for_notification_events() -> list[str]:
    event_choices: str = get_event_choices_string()
    print(
        f"""
Please select which ClickUp event notification(s) you'd
like to receive in your Zulip app.
EVENT CODES:
{event_choices}
    Or, enter * to subscribe to all events.

Here's an example input if you intend to only receive notifications
related to task, list and folder: 1,2,3
"""
    )

    code_to_events = {i + 1: events for i, events in enumerate(EVENT_CHOICES.values())}

    def process_input() -> list[str]:
        selected_codes: set[int] = set()
        input_codes_list: str = input("EVENT CODE(s): ")

        if input_codes_list.strip() == "*":
            all_events = [event for events in EVENT_CHOICES.values() for event in events]
            return all_events

        user_input = input_codes_list.split(",")
        is_input_valid = True

        for raw_code in user_input:
            event_code = raw_code.strip()
            if not event_code:
                continue
            if event_code.isdigit() and int(event_code) in code_to_events:
                selected_codes.add(int(event_code))
            else:
                is_input_valid = False
                break

        if not selected_codes or not is_input_valid:
            print("Please enter a valid set of options")
            return process_input()
        else:
            ## Codes are numbered in menu order, so sorting them lists the events that way too.
            return [event for code in sorted(selected_codes) for event in code_to_events[code]]

    return process_input()


def delete_old_webhooks(zulip_integration_url: str, api_handler: ClickUpAPIHandler) -> None:
    data: dict[str, Any] = api_handler.get_webhooks()
    for webhook in data["webhooks"]:
        if webhook["endpoint"] == zulip_integration_url:
            api_handler.delete_webhook(webhook["id"])


def display_success_msg(webhook_id: str) -> None:
    print(
        f"""
SUCCESS: Completed integrating your Zulip app with ClickUp!
webhook_id: {webhook_id}

You may delete this script or run it again to reconfigure
your integration.
"""
    )


def run(team_id: str, api_key: str, zulip_integration_url: str, replace_existing: bool) -> None:
    api_handler = ClickUpAPIHandler(api_key, team_id)
    events_payload = query_for_notification_events()
    if replace_existing:
        delete_old_webhooks(zulip_integration_url, api_handler)

    response: dict[str, Any] = api_handler.create_webhook(
        end_point=zulip_integration_url, events=events_payload
    )

    display_success_msg(response["id"])
    sys.exit(0)


def main() -> None:
    description = """
    zulip_clickup.py is a handy little script that allows Zulip users to
    quickly set up a ClickUp webhook.

    Note: The ClickUp webhook instructions available on your Zulip server
    may be outdated. Please make sure you follow the updated instructions
    at <https://zulip.com/integrations/clickup>.
    """

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--clickup-team-id",
        required=True,
        help=(
            "Your team_id is the number immediately following the base ClickUp URL. "
            "For instance, the team_id for https://app.clickup.com/25567147/home "
            "is 25567147."
        ),
    )
    parser.add_argument(
        "--clickup-api-key",
        required=True,
        help=(
            "Your personal ClickUp API token, used to register the webhook and, on "
            "the Zulip side, to fetch task and entity names. Generate one in ClickUp "
            "under Settings > ClickUp API > API Token."
        ),
    )
    parser.add_argument(
        "--zulip-webhook-url",
        required=True,
        help="The Zulip integration URL where Clickup events will be posted."
        " This URL is generated when you create your incoming webhook in Zulip"
        " (https://zulip.com/help/generate-integration-url)",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help=(
            "Before registering, delete any existing ClickUp webhook that points "
            "to this exact Zulip URL. Use when re-running the script to avoid "
            "creating duplicate webhooks."
        ),
    )

    options = parser.parse_args()
    print("Running Zulip Clickup Integration webhook creation script...")

    run(
        options.clickup_team_id,
        options.clickup_api_key,
        options.zulip_webhook_url,
        options.replace_existing,
    )


if __name__ == "__main__":
    main()

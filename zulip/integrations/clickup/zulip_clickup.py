#!/usr/bin/env python3  # noqa: EXE001
#
# A ClickUp integration script for Zulip.

import argparse
import json
import os
import re
import sys
import time
import webbrowser
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

EVENT_CHOICES: Dict[str, Tuple[str, ...]] = {
    "1": ("taskCreated", "taskUpdated", "taskDeleted"),
    "2": ("listCreated", "listUpdated", "listDeleted"),
    "3": ("folderCreated", "folderUpdated", "folderDeleted"),
    "4": ("spaceCreated", "spaceUpdated", "spaceDeleted"),
    "5": ("goalCreated", "goalUpdated", "goalDeleted"),
}


def clear_terminal_and_sleep(sleep_duration: int = 3) -> Callable[[Any], Callable[..., Any]]:
    """
    Decorator to clear the terminal and sleep for a specified duration
    before and after the execution of the decorated function.
    """
    cmd = "cls" if os.name == "nt" else "clear"

    def decorator(func: Any) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            os.system(cmd)  # noqa: S605
            result = func(*args, **kwargs)
            time.sleep(sleep_duration)
            os.system(cmd)  # noqa: S605
            return result

        return wrapper

    return decorator


def process_url(input_url: str, base_url: str) -> str:
    """
    Validates that the URL is the same the users zulip app URL.
    Returns the authorization code from the URL query
    """
    parsed_input_url = urlparse(input_url)
    parsed_base_url = urlparse(base_url)

    same_domain: bool = parsed_input_url.netloc == parsed_base_url.netloc
    auth_code = parse_qs(parsed_input_url.query).get("code")

    if same_domain and auth_code:
        return auth_code[0]
    else:
        print("Unable to fetch the auth code. exiting")
        sys.exit(1)


class ClickUpAPIHandler:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        team_id: str,
    ) -> None:
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.team_id: str = team_id
        self.API_KEY: Optional[str] = None

    def make_clickup_request(
        self, path: str, query: Dict[str, Union[str, List[str]]], method: str
    ) -> Optional[Dict[str, Any]]:
        base_url = "https://api.clickup.com/api/v2/"
        api_endpoint = urljoin(base_url, path)

        if path == "oath/token":
            encoded_query = urlencode(query).encode("utf-8")
            req = Request(api_endpoint, data=encoded_query, method=method)  # noqa: S310
        else:
            headers: Dict[str, str] = {
                "Content-Type": "application/json",
                "Authorization": self.API_KEY if self.API_KEY else "",
            }
            encoded_query = json.dumps(query).encode("utf-8")
            req = Request(  # noqa: S310
                api_endpoint, data=encoded_query, headers=headers, method=method
            )

        try:
            with urlopen(req) as response:  # noqa: S310
                if response.status != 200:
                    print(f"Error : {response.status}")
                    sys.exit(1)
                data: Dict[str, str] = json.loads(response.read().decode("utf-8"))
                return data
        except HTTPError as err:
            print(f"HTTPError occurred: {err.code} {err.reason}")
            return None

    def get_access_token(self, auth_code: str) -> None:
        """
        https://clickup.com/api/clickupreference/operation/GetAccessToken/
        """
        path = "oauth/token"
        query: Dict[str, Union[str, List[str]]] = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": auth_code,
        }
        data = self.make_clickup_request(path, query, "POST")
        if data is None or not data.get("access_token"):
            print("Unable to fetch the API key. exiting")
            sys.exit(1)
        self.API_KEY = data.get("access_token")

    def create_webhook(self, end_point: str, events: List[str]) -> Dict[str, Any]:
        """
        https://clickup.com/api/clickupreference/operation/CreateWebhook/
        """
        path = f"team/{self.team_id}/webhook"
        query: Dict[str, Union[str, List[str]]] = {
            "endpoint": end_point,
            "events": events,
        }
        data = self.make_clickup_request(path, query, "POST")
        if data is None:
            print("We're unable to create webhook at the moment. exiting")
            sys.exit(1)
        return data

    def get_webhooks(self) -> Dict[str, Any]:
        """
        https://clickup.com/api/clickupreference/operation/GetWebhooks/
        """
        path = f"team/{self.team_id}/webhook"
        data = self.make_clickup_request(path, {}, "GET")
        if data is None:
            print("We're unable to fetch webhooks at the moment. exiting")
            sys.exit(1)
        return data

    def delete_webhook(self, webhook_id: str) -> None:
        """
        https://clickup.com/api/clickupreference/operation/DeleteWebhook/
        """
        path = f"webhook/{webhook_id}"
        data = self.make_clickup_request(path, {}, "DELETE")
        if data is None:
            print("Failed to delete webhook. exiting")
            sys.exit(1)


@clear_terminal_and_sleep(1)
def query_for_integration_url() -> str:
    print(
        """
    STEP 1
    ----
    Please enter the integration URL you've just generated
    from your Zulip app settings.

    It should look similar to this:
    e.g. http://YourZulipApp.com/api/v1/external/clickup?api_key=TJ9DnIiNqt51bpfyPll5n2uT4iYxMBW9
    """
    )
    while True:
        input_url: str = input("INTEGRATION URL: ")
        if input_url:
            break
    return input_url


@clear_terminal_and_sleep(3)
def redirect_to_clickup_auth(zulip_integration_url: str, client_id: str) -> None:
    print(
        """
    STEP 2
    ----
    ClickUp authorization page will open in your browser.
    Please authorize your workspace(s).

    Click 'Connect Workspace' on the page to proceed...
    """
    )
    parsed_url = urlparse(zulip_integration_url)
    base_url: str = f"{parsed_url.scheme}://{parsed_url.netloc}"
    url: str = f"https://app.clickup.com/api?client_id={client_id}&redirect_uri={base_url}"
    time.sleep(1)
    webbrowser.open(url)


@clear_terminal_and_sleep(2)
def query_for_authorization_code(zulip_integration_url: str) -> str:
    print(
        """
    STEP 3
    ----
    After you've authorized your workspace,
    you should be redirected to your home URL.
    Please copy your home URL and paste it below.
    It should contain a code, and look similar to this:

    e.g. https://YourZulipDomain.com/?code=332KKA3321NNAK3MADS
    """
    )
    input_url: str = input("YOUR HOME URL: ")
    auth_code: str = process_url(input_url=input_url, base_url=zulip_integration_url)
    return auth_code


@clear_terminal_and_sleep(1)
def query_for_notification_events() -> List[str]:
    print(
        """
    STEP 4
    ----
    Please select which ClickUp event notification(s) you'd
    like to receive in your Zulip app.
    EVENT CODES:
          1 = task
          2 = list
          3 = folder
          4 = space
          5 = goals

    Here's an example input if you intend to only receive notifications
    related to task, list and folder: 1,2,3
    """
    )
    querying_user_input: bool = True
    selected_events: List[str] = []

    while querying_user_input:
        input_codes: str = input("EVENT CODE(s): ")
        user_input: List[str] = re.split(",", input_codes)

        input_is_valid: bool = len(user_input) > 0
        exhausted_options: List[str] = []

        for event_code in user_input:
            if event_code in EVENT_CHOICES and event_code not in exhausted_options:
                selected_events += EVENT_CHOICES[event_code]
                exhausted_options.append(event_code)
            else:
                input_is_valid = False

        if not input_is_valid:
            print("Please enter a valid set of options and only select each option once")

        querying_user_input = not input_is_valid

    return selected_events


def delete_old_webhooks(zulip_integration_url: str, api_handler: ClickUpAPIHandler) -> None:
    """
    Checks for existing webhooks with the same endpoint and delete them if found.
    """
    data: Dict[str, Any] = api_handler.get_webhooks()
    for webhook in data["webhooks"]:
        print("webhook: ", webhook)
        zulip_url_domain = urlparse(zulip_integration_url).netloc
        registered_webhook_domain = urlparse(webhook["endpoint"]).netloc

        if zulip_url_domain in registered_webhook_domain:
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


def add_query_params(url: str, params: Dict[str, List[str]]) -> str:
    parsed_url = urlparse(url)
    query_dict = parse_qs(parsed_url.query)
    query_dict.update(params)
    return parsed_url._replace(query=urlencode(query_dict)).geturl()


def run(client_id: str, client_secret: str, team_id: str) -> None:
    zulip_integration_url = query_for_integration_url()

    redirect_to_clickup_auth(zulip_integration_url, client_id)
    auth_code: str = query_for_authorization_code(zulip_integration_url)
    api_handler = ClickUpAPIHandler(client_id, client_secret, team_id)
    api_handler.get_access_token(auth_code)
    events_payload: List[str] = query_for_notification_events()
    delete_old_webhooks(
        zulip_integration_url, api_handler
    )  # to avoid setting up multiple identical webhooks

    zulip_webhook_url = add_query_params(
        zulip_integration_url,
        {
            "clickup_api_key": [api_handler.API_KEY if api_handler.API_KEY else ""],
            "team_id": [team_id],
        },
    )

    response: Dict[str, Any] = api_handler.create_webhook(
        end_point=zulip_webhook_url, events=events_payload
    )

    display_success_msg(response["id"])
    sys.exit(0)


def main() -> None:
    description = """
    zulip_clickup.py is a handy little script that allows Zulip users to
    quickly set up a ClickUp webhook.

    Note: The ClickUp webhook instructions available on your Zulip server
    may be outdated. Please make sure you follow the updated instructions
    at <https://zulip.com/integrations/doc/clickup>.
    """

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--clickup-team-id",
        required=True,
        help=(
            "Your team_id is the numbers immediately following the base ClickUp URL"
            "https://app.clickup.com/25567147/home"
            "For instance, the team_id for the URL above would be 25567147"
        ),
    )

    parser.add_argument(
        "--clickup-client-id",
        required=True,
        help=(
            "Visit https://clickup.com/api/developer-portal/authentication/#step-1-create-an-oauth-app"
            "and follow 'Step 1: Create an OAuth app' to generate client_id & client_secret."
        ),
    )
    parser.add_argument(
        "--clickup-client-secret",
        required=True,
        help=(
            "Visit https://clickup.com/api/developer-portal/authentication/#step-1-create-an-oauth-app"
            "and follow 'Step 1: Create an OAuth app' to generate client_id & client_secret."
        ),
    )

    options = parser.parse_args()
    print("Running Zulip Clickup Integration...")

    run(
        options.clickup_client_id,
        options.clickup_client_secret,
        options.clickup_team_id,
    )


if __name__ == "__main__":
    main()

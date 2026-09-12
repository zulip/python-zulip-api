# A script that automates setting up a webhook with ClickUp

This script registers a ClickUp webhook that points at your Zulip
incoming webhook bot, so that ClickUp events show up as messages in
Zulip.

Usage:

1. Gather the required credentials before running the script:
    - **ClickUp Team ID** — the number immediately following the base
      ClickUp URL. For `https://app.clickup.com/25567147/home` the team
      ID is `25567147`.
    - **ClickUp personal API token** — generate one in ClickUp under
      *Settings > ClickUp API > API Token* (it looks like `pk_...`). The script
      uses it to register the webhook, and you enter the same token when
      creating the Zulip bot so the server can resolve ClickUp entity
      IDs to human-readable names.
    - **Zulip webhook URL** — the URL generated when you create your incoming
      webhook in [Zulip](https://zulip.com/help/generate-integration-url).

2. Run the script:

    ```console
    $ python zulip_clickup.py \
        --clickup-team-id <clickup_team_id> \
        --clickup-api-key <clickup_api_key> \
        --zulip-webhook-url "<zulip_webhook_url>"
    ```

   The script asks which ClickUp events you'd like to receive, then
   registers the webhook.

3. (Optional) Pass `--replace-existing` to delete any webhook already
   pointing at the same Zulip URL before creating a new one. Use this
   when re-running the script so you don't end up with duplicate
   webhooks.

For more information, please see Zulip's documentation on how to set up
a ClickUp integration [here](https://zulip.com/integrations/clickup).

# A script that automates setting up a webhook with ClickUp

Usage :

1. Make sure you have all of the relevant ClickUp credentials before
   executing the script:
    - The ClickUp Team ID
    - The ClickUp Client ID
    - The ClickUp Client Secret

2. Execute the script :

    $ python zulip_clickup.py --clickup-team-id <clickup_team_id> \
                             --clickup-client-id <clickup_client_id> \
                             --clickup-client-secret <clickup_client_secret> \
                             --zulip-webhook-url "<zulip_webhook_url>"

For more information, please see Zulip's documentation on how to set up
a ClickUp integration [here](https://zulip.com/integrations/doc/clickup).

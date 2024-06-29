# Slack <--> Zulip bridge

This is a bridge between Slack and Zulip.

## Usage

### 1. Zulip endpoint

1. Create a generic Zulip bot, with a full name like `Slack Bot`.

2. (Important) Subscribe the bot user to the Zulip channel you'd like to bridge
   your Slack channel into.

3. Create a [Slack Webhook integration bot](https://zulip.com/integrations/doc/slack)
   to get messages form Slack to Zulip.

4. In the `zulip` section of the configuration file, fill `integration_bot_email`
   with **Integration bot**'s email. Note that this is the bot you created in
   step 3 and not in step 1.

5. Also in the `zulip` section, enter the **Generic bot's** `zuliprc`
   details (`email`, `api_key`, and `site`).

6. Moving to over the `channel_mapping` section, enter the Zulip `channel` and `topic`.
   Make sure that they match the same `channel` and `topic` you configured in steps 2
   and 3.

### 2. Slack endpoint

1. Go to the [Slack Apps menu](https://api.slack.com/apps) and open the same Slack app that
   you have use to set up the Slack Webhook integration previously.

2. Navigate to the "OAuth & Permissions" menu and scroll down to the "Scopes"
   section in the same page and make sure:
   - "Bot Token Scopes" includes: `chat:write`
   - "User Tokens Scopes" includes: `chat:write`

3. Next, also in the same menu find and note down the "Bot User OAuth Token".
   It starts with "xoxb-..." and not "xoxp" (legacy).

4. In the `slack` section of the Zulip-Slack bridge configuration file, enter the bot name
   (e.g "zulip_mirror"), token (e.g xoxb-...), and the channel ID (note: must be ID, not name).

### Running the bridge

Run Slack Bridge: `python3 run-slack-bridge`

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

<details>
<summary>Legacy: If you're still using classic Slack app, follow this instruction instead!</summary>

### 1. Zulip endpoint
1. Create a generic Zulip bot, with a full name like `Slack Bot`.
2. (Important) Subscribe the bot user to the Zulip stream you'd like to bridge your Slack
   channel into.
3. In the `zulip` section of the configuration file, enter the bot's `zuliprc`
   details (`email`, `api_key`, and `site`).
4. In the same section, also enter the Zulip `stream` and `topic`.

### 2. Slack endpoint
1. Make sure Websocket isn't blocked in the computer where you run this bridge.
   Test it at https://www.websocket.org/echo.html.
2. Go to https://api.slack.com/apps?new_classic_app=1 and create a new classic
   app (note: must be a classic app). Choose a bot name that will be put into
   bridge_with_slack_config.py, e.g. "zulip_mirror". In the process of doing
   this, you need to add oauth token scope. Simply choose `bot`. Slack will say
   that this is a legacy scope, but we still need to use it anyway. The reason
   why we need the legacy scope is because otherwise the RTM API wouldn't work.
   We might remove the RTM API usage in newer version of this bot. Make sure to
   install the app to the workspace. When successful, you should see a token
   that starts with "xoxb-...". There is also a token that starts with
   "xoxp-...", we need the "xoxb-..." one.
3. Go to "App Home", click the button "Add Legacy Bot User".
4. (Important) Make sure the bot is subscribed to the channel. You can do this by typing e.g. `/invite @zulip_mirror` in the relevant channel.
5. In the `slack` section of the Zulip-Slack bridge configuration file, enter the bot name (e.g. "zulip_mirror") and token, and the channel ID (note: must be ID, not name).

### Running the bridge

Run Legacy Slack Bridge: `python3 run-slack-bridge --legacy`

</details>

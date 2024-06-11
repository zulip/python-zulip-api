# Slack <--> Zulip bridge

This integration is a bridge with Slack, delivering messages from
Zulip into Slack. It is designed for bidirectional bridging, with the
[Slack integration](https://zulip.com/integrations/doc/slack) used to
deliver messages from Slack into Zulip.

Note that using these integrations together for bidirectional bridging
requires the updated version of the Slack integration included in
Zulip 9.4+.

## Usage

### 1. Zulip endpoint

1. Create a generic Zulip bot, with a full name like `Slack Bridge`.

2. [Subscribe](https://zulip.com/help/manage-user-channel-subscriptions#subscribe-a-user-to-a-channel)
   the bot user to the Zulip channel(s) you'd like to bridge with
   Slack.

3. Create a [Slack webhook integration bot](https://zulip.com/integrations/doc/slack)
   to get messages from Slack to Zulip. Make sure to follow the additional instruction
   for setting up a Slack bridge.

4. In the `zulip` section of the `bridge_with_slack_config.py`
   configuration file, the bot's `zuliprc` details (`email`,
   `api_key`, and `site`).

5. In the `channel_mapping` section, enter the Zulip `channel` and
   `topic` that you'd like to use for each Slack channel.  Make sure
   that they match the same `channel` and `topic` you configured in
   steps 2 and 3.

### 2. Slack endpoint

1. Go to the [Slack Apps menu](https://api.slack.com/apps) and open the same Slack app
   that you used to set up the Slack Webhook integration previously.

2. Navigate to the "OAuth & Permissions" menu and scroll down to the "Scopes"
   section in the same page. Make sure "Bot Token Scopes" includes: `chat:write`

3. Next, also in the same menu find and note down the "Bot User OAuth Token".
   It starts with "xoxb-..." and not "xoxp".

4. In the `slack` section of `bridge_with_slack_config.py`, enter the
   bot name (e.g "slack_bridge"), token (e.g xoxb-...), and the
   channel ID (note: must be ID, not name).

### Running the bridge

Run `python3 run-slack-bridge`

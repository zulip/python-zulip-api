config = {
    "zulip": {
        "email": "zulip-bot@email.com",
        "api_key": "put api key here",
        "site": "https://chat.zulip.org",
    },
    "slack": {
        "username": "slack_username",
        "token": "xoxb-your-slack-token",
    },
    # Mapping between Slack channels and Zulip stream-topic's.
    # You can specify multiple pairs.
    "channel_mapping": {
        # Slack channel; must be channel ID
        "C5Z5N7R8A": {
            # Zulip stream
            "stream": "test here",
            # Zulip topic
            "topic": "<- slack-bridge",
        },
    },
}

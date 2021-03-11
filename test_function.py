#!/usr/bin/env python3

import zulip

# Pass the path to your zuliprc file here.
client = zulip.Client(config_file="~/zuliprc")

# Get all streams that the user is subscribed to
result = client.list_subscriptions()
print(result)

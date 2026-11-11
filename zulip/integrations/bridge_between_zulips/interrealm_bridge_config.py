config = {
    "bot_1": {
        # Either specify the path to a zuliprc file:
        # "config_file": "~/zuliprc-realm1",
        # Or specify credentials explicitly:
        "email": "tunnel-bot@realm1.zulipchat.com",
        "api_key": "key1",
        "site": "https://realm1.zulipchat.com",
        "stream": "bridges",
        "subject": "<- realm2",
    },
    "bot_2": {
        # Either specify the path to a zuliprc file:
        # "config_file": "~/zuliprc-realm2",
        # Or specify credentials explicitly:
        "email": "tunnel-bot@realm2.zulipchat.com",
        "api_key": "key2",
        "site": "https://realm2.zulipchat.com",
        "stream": "bridges",
        "subject": "<- realm1",
    },
}

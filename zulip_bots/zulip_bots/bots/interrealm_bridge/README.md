# Inter-realm bot

Let `realm_1` be the first realm, `realm_2` be the second realm.  Let `bot_1` be
the relay bot in `realm_1`, `bot_2` be the relay bot in `realm_2`.

This bot relays each message received at a specified subject in a specified
stream from `realm_1` to a specified subject in a specified stream in `realm_2`.

Steps to create an inter-realm bridge:
1. Register a generic bot (`bot_1`) in `realm_1`
2. Enter the api info of `bot_1` into the config file (interrealm_bridge_config.py)
3. Create a stream in `realm_1` (`stream_1`) and a subject for the bridge
4. Make sure `bot_1` is subscribed to `stream_1`
5. Enter the stream and the subject into the config file.
6. Do step 1-5 but for `bot_2` and with all occurrences of `_1` replaced with `_2`

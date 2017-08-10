# Matrix <--> Zulip bridge

This also enables a Zulip topic to be federated !

## Usage

### 1. Zulip endpoint
1. Create a generic Zulip bot
2. (don't forget this step!) Make sure the bot is subscribed to the relevant stream
2. Enter the bot's email and api_key into matrix_bridge_config.py
3. Enter the destination subject and realm into matrix_bridge_config.py

### 2. Matrix endpoint
1. Create a user
2. Enter the user's username and password into matrix_bridge_config.py
3. Enter the host and room_id into matrix_bridge_config.py

After the steps above have been completed, run `python matrix_bridge.py` to
start the mirroring.

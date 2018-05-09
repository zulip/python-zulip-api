# Matrix <--> Zulip bridge

This acts as a bridge between Matrix and Zulip. It also enables a Zulip topic to be federated.

## Usage

### For IRC bridges

Matrix has been bridged to the listed
[IRC networks](https://github.com/matrix-org/matrix-appservice-irc/wiki/Bridged-IRC-networks),
where the 'Room alias format' refers to the `room_id` for the corresponding IRC channel.

For example, for the freenode channel `#zulip-test`, the `room_id` would be
`#freenode_#zulip-test:matrix.org`.

Hence, this can also be used as a IRC <--> Zulip bridge.

## Steps to configure the Matrix bridge

### 1. Zulip endpoint
1. Create a generic Zulip bot
2. (don't forget this step!) Make sure the bot is subscribed to the relevant stream
2. Enter the bot's email and `api_key` into `matrix_bridge_config.py`
3. Enter the destination subject, realm and site in `matrix_bridge_config.py`

### 2. Matrix endpoint
1. Create a user on [matrix.org](https://matrix.org/)
2. Enter the user's username and password into `matrix_bridge_config.py`
3. Enter the host and `room_id` into `matrix_bridge_config.py`

After the steps above have been completed, run `python matrix_bridge.py` to
start the mirroring.

## Note

There are certain
[IRC channels](https://github.com/matrix-org/matrix-appservice-irc/wiki/Channels-from-which-the-IRC-bridge-is-banned)
where the messages from Zulip cannot be forwarded to
IRC due to a ban on the Matrix bot.

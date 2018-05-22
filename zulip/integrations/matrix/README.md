# Matrix <--> Zulip bridge

This acts as a bridge between Matrix and Zulip. It also enables a
Zulip topic to be federated between two Zulip servers.

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
1. Create a generic Zulip bot, with a full name like `IRC Bot`.
2. Subscribe the bot user to the stream you'd like to mirror your IRC
   channel into.
3. Enter the bot's `zuliprc` details (`email`, `api_key`, and `site`)
   into `matrix_bridge_config.py`
4. Enter the destination topic, stream and site in `matrix_bridge_config.py`

### 2. Matrix endpoint
1. Create a user on [matrix.org](https://matrix.org/), preferably with
   a formal name like to `zulip-bot`.
2. Enter the user's username and password into `matrix_bridge_config.py`
3. Enter the host and `room_id` into `matrix_bridge_config.py`

After the steps above have been completed, run `python matrix_bridge.py` to
start the mirroring service.

## Caveats for IRC mirroring

There are certain
[IRC channels](https://github.com/matrix-org/matrix-appservice-irc/wiki/Channels-from-which-the-IRC-bridge-is-banned)
where the Matrix.org IRC bridge has been banned for technical reasons.
You can't mirror those IRC channels using this integration.

# Matrix <--> Zulip bridge

This acts as a bridge between Matrix and Zulip.

### Enhanced Features
- Supporting multiple (Zulip topic, Matrix channel)-pairs.
- Handling files according to their mimetype.


## Installation

Run `pip install -r requirements.txt` in order to install the requirements.

In case you'd like encryption to work, you need pip to install the `matrix-nio`
package with e2e support:
- First, you need to make sure that the development files of the `libolm`
  C-library are installed on your system! See [the corresponding documentation
  of matrix-nio](https://github.com/poljar/matrix-nio#installation) for further
  information on this point.
- `pip install matrix-nio[e2e]`


## Steps to configure the Matrix bridge

To obtain a configuration file template, run the script with the
`--write-sample-config` option to obtain a configuration file to fill in the
details mentioned below. For example:

* If you installed the `zulip` package: `zulip-matrix-bridge --write-sample-config matrix_bridge.conf`

* If you are running from the Zulip GitHub repo: `python matrix_bridge.py --write-sample-config matrix_bridge.conf`

### 1. Zulip endpoint
1. Create a generic Zulip bot, with a full name such as `Matrix Bot`.
2. The bot is able to subscribe to the necessary streams itself if they are
   public. (Note that the bridge will not try to create streams in case they
   do not already exist. In that case, the bridge will fail at startup.)
   Otherwise, you need to add the bot manually.
3. In the `zulip` section of the configuration file, enter the bot's `zuliprc`
   details (`email`, `api_key`, and `site`).
4. In the same section, also enter the Zulip `stream` and `topic`.

### 2. Matrix endpoint
1. Create a user on the matrix server of your choice, e.g. [matrix.org](https://matrix.org/),
   preferably with a descriptive name such as `zulip-bot`.
2. In the `matrix` section of the configuration file, enter the user's Matrix
   user ID `mxid` and password. Please use the Matrix user ID ([MXID](https://matrix.org/faq/#what-is-a-mxid%3F))
   as format for the username!
3. Create the Matrix room(s) to be bridged in case they do not exits yet.
   Remember to invite the bot to private rooms! Otherwise, this error will be
   thrown: `Matrix bridge error: JoinError: M_UNKNOWN No known servers`.
4. Enter the `host` and `room_id` into the same section.
   In case the room is private you need to use the `Internal room ID` which has
   the format `!aBcDeFgHiJkLmNoPqR:example.org`.
   In the official Matrix client [Element](https://github.com/vector-im), you
   can find this `Internal room ID` in the `Room Settings` under `Advanced`.

### Adding more (Zulip topic, Matrix channel)-pairs
1. Create a new section with a name starting with `additional_bridge`.
2. Add a `room_id` for the Matrix side and a `stream` and a `topic` for the
   Zulip side.

Example:
```
[additional_bridge1]
room_id = #zulip:matrix.org
stream = matrix test
topic = matrix test topic
```


## Running the bridge

After the steps above have been completed, assuming you have the configuration
in a file called `matrix_bridge.conf`:

* If you installed the `zulip` package: run `zulip-matrix-bridge -c matrix_bridge.conf`

* If you are running from the Zulip GitHub repo: run `python matrix_bridge.py -c matrix_bridge.conf`


## Notes regarding IRC

### Usage for IRC bridges

This can also be used to indirectly bridge between IRC and Zulip.

Matrix has been bridged to the listed
[IRC networks](https://matrix-org.github.io/matrix-appservice-irc/latest/bridged_networks.html),
where the 'Room alias format' refers to the `room_id` for the corresponding IRC channel.

For example, for the Libera Chat channel `#zulip-test`, the `room_id` would be
`#zulip-test:libera.chat`.

### Caveats for IRC mirroring

There are certain
[IRC channels](https://github.com/matrix-org/matrix-appservice-irc/wiki/Channels-from-which-the-IRC-bridge-is-banned)
where the Matrix.org IRC bridge has been banned for technical reasons.
You can't mirror those IRC channels using this integration.


## TODO

- Adding support for editing and deleting messages?
- Handling encryption on the Matrix side (may need further discussion).

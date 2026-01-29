# Zulip IRC Integration

Mirror messages between an IRC channel and a Zulip channel in real-time!

{start_tabs}

1.  {!download-python-bindings.md!}

1.  {!install-requirements.md!}

1.  Register a nick that ends with the suffix `_zulip` on your IRC server.

1.  {!create-a-generic-bot.md!}

1.  Download the `zuliprc` configuration file of your bot by clicking the
    download (<i class="fa fa-download"></i>) icon under the bot's name, and
    save to `~/.zuliprc`.

1.  [Subscribe the bot][subscribe-channels] to the Zulip channel where IRC
    messages should be mirrored.

1.  Begin mirroring messages between the IRC channel and the Zulip channel
    by running the `irc-mirror.py` script with the
    [required command-line arguments](#required-arguments). Use the
    [optional arguments](#optional-arguments) to configure the mirroring
    behavior.

    Here's an example command that mirrors messages between the
    **#python-mypy** channel on the `irc.freenode.net` server and the "mypy"
    topic on the **#irc-discussions** channel on Zulip:

    ```
    python {{ integration_path }}/irc-mirror.py \
    --irc-server=irc.freenode.net --channel='#python-mypy' --nick-prefix=irc_mirror \
    --stream='irc-discussions' --topic='mypy'
    ```

1.  Messages will be mirrored only when the terminal session with the bot
    remains open. Consider using `screen` to run the bot in the background.
    You can restart the integration at any time by re-running the
    `irc-mirror.py` script.

{end_tabs}

You're done! Messages in your Zulip channel may look like:

![IRC message on Zulip](/static/images/integrations/irc/001.png)

Messages in your IRC channel may look like:

![Zulip message on IRC](/static/images/integrations/irc/002.png)

[subscribe-channels]: /help/manage-user-channel-subscriptions#subscribe-a-user-to-a-channel

### Configuration options

The integration script accepts the following command-line arguments:

#### Required arguments

- `--irc-server`: The IRC server to mirror.

- `--nick-prefix`: Your registered IRC nick without the `_zulip` suffix.

- `--channel`: The IRC channel to mirror.

- `--stream`: The name of the Zulip channel you want to mirror. The default
  channel name is **#general**.

#### Optional arguments

- `--topic`: The name of the Zulip topic you want to receive and send
  messages in. The default topic name is "IRC".

- `--port`: The port to connect to the IRC server on. Defaults to 6667.

- `--nickserv-pw`: Password corresponding to the IRC nick.

- `--sasl-password`: Password for SASL authentication.

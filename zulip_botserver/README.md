```
zulip-botserver --config-file <path to botserverrc> --hostname <address> --port <port>
```

Example: `zulip-botserver --config-file ~/botserverrc`

This program loads the bot configurations from the
config file (`botserverrc`, here) and loads the bot modules.
It then starts the server and fetches the requests to the
above loaded modules and returns the success/failure result.

The `--hostname` and `--port` arguments are optional, and default to
127.0.0.1 and 5002 respectively.

The format for a configuration file is:

    [helloworld]
    key=value
    email=helloworld-bot@zulip.com
    site=http://localhost
    token=abcd1234
    bot-config-file=helloworld.conf

Is passed `--use-env-vars` instead of `--config-file`, the
configuration can instead be provided via the `ZULIP_BOTSERVER_CONFIG`
environment variable.  This should be a JSON-formatted dictionary of
bot names to dictionary of their configuration; for example:

    ZULIP_BOTSERVER_CONFIG='{"helloworld":{"email":"helloworld-bot@zulip.com","key":"value","site":"http://localhost","token":"abcd1234"}}' \
      zulip-botserver --use-env-vars

## Running a custom bot from a Python file

Custom bots do not need to be copied into the `zulip_bots` package. The
Botserver can load an existing `.py` file that defines `handler_class`, as
in the [Hello World bot](../zulip_bots/zulip_bots/bots/helloworld/helloworld.py).

For a single custom bot, save a configuration file such as `botserverrc`:

```ini
[my_bot]
email=my-bot@example.com
key=YOUR_BOT_API_KEY
site=https://your-organization.zulipchat.com
token=YOUR_OUTGOING_WEBHOOK_TOKEN
```

Replace the example values with your bot's email, API key, organization URL,
and outgoing webhook token. Keep this file private; it contains credentials.

Pass the path to your bot file using `--bot-name`:

```sh
zulip-botserver --config-file ./botserverrc --bot-name ./my_bot.py
```

In single-bot mode, the Botserver uses the configuration section matching
`--bot-name`, or the first section if there is no match. In this example,
it uses `[my_bot]`. Other sections are ignored.

Relative file paths are resolved from the directory where you run the
command, not from the configuration file's directory. To run the command
from another directory, use absolute paths:

```sh
zulip-botserver --config-file /path/to/botserverrc --bot-name /path/to/my_bot.py
```

### Troubleshooting custom bot loading

- If the Botserver reports that the bot does not exist, check that the
  path passed to `--bot-name` points to an existing file ending in `.py`.
- If your bot imports third-party packages, install them in the Python
  environment used to run `zulip-botserver`.
- If your bot imports your own modules, make those modules importable in
  the same environment. For example, add their containing directory to
  `PYTHONPATH` for the command:

  ```sh
  PYTHONPATH=/path/to/helpers zulip-botserver --config-file /path/to/botserverrc --bot-name /path/to/my_bot.py
  ```

  Loading a bot by its file path does not automatically add its directory
  to Python's module search path.

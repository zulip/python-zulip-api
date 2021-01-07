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

Is passed `--use-env-vars` instead of `--config-file`, the
configuration can instead be provided via the `ZULIP_BOTSERVER_CONFIG`
environment variable.  This should be a JSON-formatted dictionary of
bot names to dictionary of their configuration; for example:

    ZULIP_BOTSERVER_CONFIG='{"helloworld":{"email":"helloworld-bot@zulip.com","key":"value","site":"http://localhost","token":"abcd1234"}}' \
      zulip-botserver --use-env-vars

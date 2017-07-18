```
zulip-bot-server --config-file <path to flaskbotrc> --hostname <address> --port <port>

```

Example: `zulip-bot-server --config-file ~/flaskbotrc`

This program loads the bot configurations from the
config file (flaskbotrc here) and loads the bot modules.
It then starts the server and fetches the requests to the
above loaded modules and returns the success/failure result.

Please make sure you have a current flaskbotrc file with the
configurations of the required bots.
Hostname and Port are optional arguments. Default hostname is
127.0.0.1 and default port is 5002.

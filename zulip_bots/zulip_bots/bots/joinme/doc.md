# Joinme bot

The Joinme bot posts a link to a Joinme call when being mentioned.

## Setup

1. See [here](https://developer.join.me/docs) for setting up an account and
   registering the app.
2. open `bots/joinme/joinme.conf` and change the values of key, secret and the
   callback url to the ones you created.
3. See [here](https://zulipchat.com/api/running-bots#running-a-bot) for description
   on how to run a bot.
4. When using `zulip-run-bot joinme --config-file ~/zuliprc-joinme` to run joinme,
   don't forget to include `--bot-config-file` and the path to `joinme.conf` at
   the end. e.g.`zulip-run-bot joinme --config-file ~/zuliprc-joinme --bot-config
   -file ~/zulip/python-zulip-api/zulip_bots/zulip_bots/bots/joinme/joinme.conf`

## Usage

1. @-mention it first and it will give out a link which asks for permission
   to view the personal url and to start a new meeting. Login is required.

2. Then @-mention the bot again with the url shown in the browser after
   authorising Joinme.

3. The url will expire in one minute, if it happens repeat step 1.

4. Finally the bot will post a link to the new meeting created.

See [example](https://github.com/itstakenalr/python-zulip-api/blob/task-joinme/zulip_bots/zulip_bots/bots/joinme/assets/1.JPG)

# Joinme bot

The Joinme bot posts a link to a Joinme call when being mentioned.

## Setup

See [here](https://zulipchat.com/api/running-bots#running-a-bot) for description
on how to run a bot.

## Usage

1. @-mention it first and it will give out a link which asks for permission
   to view the personal url and to start a new meeting. Login is required.

2. Then @-mention the bot again with the url shown in the browser after
   authorising Joinme.

3. The url will expire in one minute, if it happens repeat step 1.

4. Finally the bot will post a link to the new meeting created.

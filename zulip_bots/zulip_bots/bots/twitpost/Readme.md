# Twitpost Bot

Twitpost bot is a Zulip bot to tweet from zulip chat.

To use twitpost bot, you can simply call it with `@twitpost` followed
by a keyword `tweet` followed by the content to be tweeted.
For example:

`@twitpost tweet hey batman`

# Setup

Before starting using the bot, you will need:

1. consumer_key
2. consumer_secret
3. access_token
4. access_token_secret

To obtain these 4 keys, follow the following steps :

1. Login on [Twitter Application Management](https://apps.twitter.com/) using your Twitter account credentials.
2. Create a new Twitter app in the [Twitter Application Management](https://apps.twitter.com/)
3. Provide the required details (Name, Description and Website).
4. Open your app and click on `Keys and Access Tokens`.
5. This completes creation of Twitter app to get the 4 required keys.
6. Take a look at configuration section to configure the bot.

# Configuration

Enter the 4 keys in the respective field in `twitter.ini` file.

Run this bot as described in [here](https://zulip.com/api/running-bots#running-a-bot).

## Usage

`@twitpost tweet`

- This command tweets the given content to Twitter.
- Example Usage: `@twitpost tweet hey batman`, `@twitpost tweet hello world!`
- Sample Output:

`Tweet Posted
https://twitter.com/jasoncosta/status/243145735212777472`

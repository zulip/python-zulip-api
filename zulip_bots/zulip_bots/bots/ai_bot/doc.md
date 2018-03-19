# AI Bot

The AI Bot is a Zulip bot that can be customized by updating the AIML files
for various different tasks like creating trivias, a chat bot, answering queries.
The link is returned to the same stream it was @mentioned in.

Using the AI bot is as simple as mentioning @\<ai-bot-name\>,
followed by the query:

```
@<stackoverflow-bot-name> <query>
```

## Setup

Beyond the typical obtaining of the zuliprc file, no extra setup is required to use the AI Bot

## Usage

1. ```@<ai-bot-name> <query>``` -

Gives the most appropriate answer to the query.

<br>

2. If there are no questions related to the query,
the bot will respond with an error message:

    ```Sorry. I didn't quite get that.```

<br>

3. If no query is provided, the bot will return the help text:

    ```Please enter your message after @mention-bot to chat with AI Bot```

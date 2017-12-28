# IDoneThis bot

The IDoneThis bot is a Zulip bot that can fetch entries from the set
organization from [IDoneThis](https://home.idonethis.com/).

To use the IDoneThis bot, you can simply call it with `@IDoneThis` followed
by a number for the number of tasks you want to see, like so:

```
@IDoneThis 5
```

## Setup

Before you can proceed further, you'll need to go to the
[IDoneThis website](https://beta.idonethis.com/login), and get an 
API key.

1. Log in or create an account on I Done This.
2. Create an Organization and then create a team within the organization.
3. Go into your team, and find your team's ID within the URL of the page.
4. Go into your account settings and find your API Token.
5. And you're done! You should now have an API key and a Team ID.
6. Open up `zulip_bots/bots/idonethis/idonethis.conf` in an editor and
   and change the value of the `key` attribute to the API key you 
   generated above and the value of the `team` attribute to your Team ID.

{!running-a-bot.md!}

## Usage

1. `@IDoneThis <number>` - This command will fetch the last `number` of tasks
   completed in your team. Example usage: `@IDoneThis 10`

2. If your keyword is unrecognizable, the bot will
   respond with an error message.

3. If there's a connection error, the bot will respond with an
   error message.

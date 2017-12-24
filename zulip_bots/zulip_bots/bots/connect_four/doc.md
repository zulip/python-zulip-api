# Connect Four Bot

The Connect Four bot is a Zulip bot that will allow users
to play a game of Connect Four against either another user,
or the computer. All games are run within private messages
sent between the user(s) and the bot.

Starting a new game with another user requires a simple command,
and the desired opponent's zulip-related email adress:

```
@<bot-name> start game with user@example.com
```

Starting a game with the computer is even simpler:

```
@<bot-name> start game with computer
```

**See Usage for a complete list of commands**

*Due to design contraints, the Connect Four Bot
can only run a single game at a time*

## Setup

To set moderators for the bot, modify the connect_four.conf
file as shown:

superusers = ["user@example.com", "user@example2.com", ...]

Moderators can run ```force reset``` in case any user abuse the bot

## Usage

*All commands should be prefaced with* ```@<bot-name>```

1. ```help``` : provides the user with relevant
commands for first time users.

2. ```status``` : due to design contraints, the
bot can only run a single game at a time. This command allows
the user to see the current status of the bot, including
whether or not the bot is running a game, if the bot is waiting
for a player to accept an invitation to play, as well as who
is currently using the bot.

3. ```start game with user@example.com``` : provided
that the bot is not running a game, this command can be used to
invite another player to play a game of Connect Four with the user.
Note that the user must be specified with their email adress, not
their username.

4. ```start game with computer``` : provided that the bot is not
running a game, this command will begin a single player game
between the user and a computer player. Note that the currently
implemented computer plays randomly.

5. ```accept``` : a command that can only be run by an invited
player to accept an invitation to play Connect Four against
another user.

6. ```decline``` : a command that can only be run by an invited
player to decline an invitation to play Connect Four against
another user.

7. ```cancel game``` : a command that can only be run by the
inviter to withdraw their invitation to play. Especially
useful if a player does not respond to an invitation for a
long period of time.

8. ```move <column-number>``` : during a game, a player may run
this command on their turn to place a token in the specified
column.

9. ```quit``` : responds with a confirmation message that asks
the user to confirm they wish to forfeit the game.

10. ```confirm quit``` : causes the user that runs this command
to forfeit the game.

11. ```force reset``` : a command that can only be run by the bot
owner and moderators (see 'Usage' for specifying). Destroys any
game currently being run if users are abusing the bot

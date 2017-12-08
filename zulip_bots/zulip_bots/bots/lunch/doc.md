# Lunch Bot 🍛
A small Zulip bot for organizing lunch with your friends and coworkers. To call
the bot simply use:

```
@lunch <user if applicable> <command>
```

## Usage
Most of lunch bot's commands can be applied to both the sender or another user
in the same server. To do so, write the user's @ before the command like in the
following examples:

`I want <item>` - Adds <item> to the sender's list of items

`<user> wants <item>` - Adds <item> to the <user>'s list of items

`<user> I want that` - Adds every item in <user>'s list of items to the sender's
list of items

`<user> remove <item>` - Removes <item> from the sender's (or <user> if
specified) list of items

`<user remove all` - Removes all items from the sender's (or <user> if specified
) list of items

`orders` - Show all orders

`<user> order` - Shows all items in the sender's (or <user> if specified) list
of items

`who should <verb>(?)` - Randomly selects a user from the orders list

`help` - Shows help (this section)

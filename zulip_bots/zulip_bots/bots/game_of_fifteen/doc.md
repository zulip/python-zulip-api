# game_of_fifteen bot

Game of Fifteen bot is a bot designed to let you play a game of fifteen. To summon it, simply type `@game_of_fifteen`,
like so:

```
@game_of_fifteen
```

Run this bot as described in [here](https://zulipchat.com/api/running-bots#running-a-bot).

## Usage

The goal of the game is to arrange all numbers from smallest to largest, starting with the grey question mark in the upper left corner, and then moving through each row until we hit the end.

`move <tile1> <tile2>` - This command is used to pick which number to switch with the grey question mark. Only pieces adjacent to the grey question mark may be moved.

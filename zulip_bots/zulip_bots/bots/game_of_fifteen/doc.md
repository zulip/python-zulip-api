# Game of Fifteen bot

This bot is designed to let you play a [game of fifteen](https://en.wikipedia.org/wiki/15_puzzle).

The goal of the game is to arrange all numbers from smallest to largest,
starting with the grey question mark in the upper left corner, and then
moving through each row till one reaches the end.

## Usage

To start a new game, simply type:

```
@game_of_fifteen
```

`move <tile1> <tile2>` - This command is used to pick which number to
    switch with the grey question mark. Only pieces adjacent to the
    grey question mark may be moved.

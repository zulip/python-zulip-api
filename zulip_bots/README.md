# Zulip bots

This directory contains the source code for the `zulip_bots` PyPI package.

The Zulip documentation has guides on [using Zulip's bot system](
https://chat.zulip.org/api/running-bots)
and [writing your own bots](
https://chat.zulip.org/api/writing-bots).

## Directory structure

```shell
zulip_bots  # This directory
├───zulip_bots  # `zulip_bots` package.
│   ├───bots/  # Actively maintained and tested bots.
│   ├───game_handler.py  # Handles game-related bots.
│   ├───lib.py  # Backbone of run.py
│   ├───provision.py  # Creates a development environment.
│   ├───run.py  # Used to run bots.
│   ├───simple_lib.py  # Used for terminal testing.
│   ├───test_lib.py  # Backbone for bot unit tests.
│   ├───test_run.py  # Unit tests for run.py
│   └───bot_shell.py  # Used to test bots in the command line.
└───setup.py  # Script for packaging.
```

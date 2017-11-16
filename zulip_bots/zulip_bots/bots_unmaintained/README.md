# Unmaintained bots

This directory contains bots that are currently not maintained by the Zulip
community. They are untested and potentially buggy or completely nonfunctional.
We only know that they worked at the time of their creation.

We see potential in every bot included in this directory. Many were moved simply
because they didn't contain automated tests. Feel free to use or revive
these bots.

## Reviving a bot

To revive an unmaintained bot, go through our [Writing bots](
https://chat.zulip.org/api/writing-bots) guide and check if
the bot meets the outlined criteria.
In particular, this means that the bot should:
* contain automated tests.
* be well-documented, with usage examples.
* provide a command set reasonably easy and convenient to use for a human.

Once a bot fulfills all the criteria, feel free to submit a pull request to add it
to the `bots` directory. We are happy to include it there.

# Architecture

This document provides a big picture of Zulip's bot architecture.

## Design goals

The goal is to have a common framework for hosting a bot that reacts
to messages in any of the following settings:

* Run as a long-running process using `call_on_each_event`.

* Run via a simple web service that can be deployed to PAAS providers
  and handles outgoing webhook requests from Zulip.

* Embedded into the Zulip server (so that no hosting is required),
  which would be done for high quality, reusable bots; we would have a
  nice "bot store" sort of UI for browsing and activating them.

* Run locally by our technically inclined users for bots that require
  account specific authentication, for example: a Gmail bot that lets
  one send emails directly through Zulip.

## Portability

The core logic of a bot is implemented in a class
that inherits from `ExternalBotHandler`.
Creating a handler class for each bot allows your bot
code to be more portable. For example, if you want to
use your bot code in some other kind of bot platform, then
if all of your bots conform to the `handler_class` protocol,
you can write simple adapter code to use them elsewhere.

## Other approaches

You can still use the full Zulip API to create custom
solutions. The hope, though, is that this architecture
will make writing simple bots a quick and easy process.

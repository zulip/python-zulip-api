# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/).

## [0.5.5] - 2018-09-25
## Changed
- Changed integrations/trello/zulip_trello.py to be a standalone script that
  can be run from anywhere.
- Changed integrations/trello/zulip_trello.py to not rely on any external
  config files or logging.

## [0.5.4] - 2018-08-31
## Changed
- Renamed `Client.get_presence()` to `Client.get_user_presence()`.

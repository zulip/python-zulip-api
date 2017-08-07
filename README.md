# Zulip API

This repository contains the source code for Zulip's PyPI packages:

* `zulip`: [PyPI package](https://pypi.python.org/pypi/zulip/)
  for Zulip's API bindings.
* `zulip_bots`: [PyPI package](https://pypi.python.org/pypi/zulip-bots)
  for Zulip's bots and bots API.
* `zulip_botserver`: [PyPI package](https://pypi.python.org/pypi/zulip-botserver)
  for Zulip's Flask bot server.

## Development

1. Fork and clone the Git repo:
   `git clone https://github.com/<your_username>/python-zulip-api.git`

2. Make sure you have [pip](https://pip.pypa.io/en/stable/installing/)
   and [virtualenv](https://virtualenv.pypa.io/en/stable/installation/)
   installed.

3. `cd` into the repository cloned earlier:
   `cd python-zulip-api`

4. Run:
   ```
   ./tools/provision
   source ./zulip-api-py2-venv/bin/activate
   ```

5. You should now be able to run all the tests within this virtualenv.

### Running tests

You can run the tests for the `zulip_bots` package by typing:

`./tools/test-bots`

You can run the tests for the `zulip_botserver` by typing:

`python -m unittest discover -v ./zulip_botserver`

To run the linter, type:

`./tools/lint`

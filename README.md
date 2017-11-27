# Zulip API

![Build status](https://travis-ci.org/zulip/python-zulip-api.svg?branch=master)
[![Coverage status](https://img.shields.io/codecov/c/github/zulip/python-zulip-api/master.svg)](
https://codecov.io/gh/zulip/python-zulip-api)

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
   ```
   This sets up a virtual Python environment in `zulip-api-py<your_python_version>-venv`,
   where `<your_python_version>` is your default version of Python. If you would like to specify
   a different Python version, run
   ```
   ./tools/provision -p <path_to_your_python_version>
   ```

5. The above step, if successful, will tell you the command to "source" your
   virtual environment.  Run that command!

6. You should now be able to run all the tests within this virtualenv.

### Running tests

To run the tests for

* *zulip*: run `./tools/test-zulip`

* *zulip_bots*: run `./tools/test-bots`

* *zulip_botserver*: run `./tools/test-botserver`

To run the linter, type:

`./tools/lint`

To check the type annotations, run:

`./tools/run-mypy`

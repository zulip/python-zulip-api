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
  for Zulip's Flask Botserver.

The source code is written in *Python 3*.

## Development

This is part of the Zulip open source project; see the
[contributing guide](https://zulip.readthedocs.io/en/latest/overview/contributing.html)
and [commit guidelines](https://zulip.readthedocs.io/en/latest/contributing/version-control.html).

1. Fork and clone the Git repo:
   `git clone https://github.com/<your_username>/python-zulip-api.git`

2. Make sure you have [pip](https://pip.pypa.io/en/stable/installing/)
   and [virtualenv](https://virtualenv.pypa.io/en/stable/installation/)
   installed.

3. `cd` into the repository cloned earlier:
   `cd python-zulip-api`

4. Run:
   ```
   python3 ./tools/provision
   ```
   This sets up a virtual Python environment in `zulip-api-py<your_python_version>-venv`,
   where `<your_python_version>` is your default version of Python. If you would like to specify
   a different Python version, run
   ```
   python3 ./tools/provision -p <path_to_your_python_version>
   ```

5. If that succeeds, it will end with printing the following command:
   ```
   source /.../python-zulip-api/.../activate
   ```
   You can run this command to enter the virtual environment.
   You'll want to run this in each new shell before running commands from `python-zulip-api`.

6. Once you've entered the virtualenv, you should see something like this on the terminal:
   ```
   (zulip-api-py3-venv) user@pc ~/python-zulip-api $
   ```
   You should now be able to run any commands/tests/etc. in this
   virtual environment.

### Running tests

To run the tests for

* *zulip*: run `./tools/test-zulip`

* *zulip_bots*: run `./tools/test-lib && ./tools/test-bots`

* *zulip_botserver*: run `./tools/test-botserver`

To run the linter, type:

`./tools/lint`

To check the type annotations, run:

`./tools/run-mypy`

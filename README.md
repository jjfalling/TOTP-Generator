[![Python Tests](https://github.com/jjfalling/TOTP-Generator/actions/workflows/python-tests.yml/badge.svg?branch=master)](https://github.com/jjfalling/TOTP-Generator/actions/workflows/python-tests.yml)
[![codecov](https://codecov.io/gh/jjfalling/TOTP-Generator/branch/master/graph/badge.svg)](https://codecov.io/gh/jjfalling/TOTP-Generator)

# TOTP Generator
Simple Python TOTP code generator that stores TOTP secrets in your keyring.
Install with `pip install totp-generator`

As of version 3 this requires python 3.7+. Version 2.x is tested to run on python 2.7 - 3.8, however this major version
will not receive any updates.

Supported keyrings can be found [here](https://pypi.python.org/pypi/keyring#what-is-python-keyring-lib). You can also
specify the [keyring settings](https://pypi.python.org/pypi/keyring#customize-your-keyring-by-config-file) in a config
file. Run `totp_generator` with the -d flag for the config root path and the current keyring service.

setproctitle is an optional dependency due permission and dependency requirements on some systems. Install with
`pip install totp-generator[proctitle]` to install this dependancy and enable setting the process name. This feature
is useful for some uses with some keyrings such as the OSX Keychain.

Run `totp_generator` with the --help flag for more information.


#### Development
This project uses semantic versioning (major.minor.patch).

Install the test requirements with `pip install ".[test]"
`. Run the tests with pytest (see https://github.com/jjfalling/TOTP-Generator/blob/master/.github/workflows/python-tests.yml for command).

To create a new build:
 * Bump the version in totp_generator/\_\_init__.py
 * Run `python setup.py upload`
 * Add a new Github release with the git tag that setup.py created (same as the new version number).

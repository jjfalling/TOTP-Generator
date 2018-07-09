![Test Status](https://travis-ci.org/jjfalling/TOTP-Generator.svg?branch=master)
![Dependency Status](https://pyup.io/repos/github/jjfalling/TOTP-Generator/shield.svg)

# TOTP Generator
Simple Python TOTP code generator that stores TOTP secrets in your keyring.

Supported keyrings can be found [here](https://pypi.python.org/pypi/keyring#what-is-python-keyring-lib). You can also specify the [keyring settings](https://pypi.python.org/pypi/keyring#customize-your-keyring-by-config-file
) in a config file. Run with the -d flag for the config root path and the current keyring service.

setproctitle is an optional dependency due permission and dependency requirements on some systems. Install with `pip install totp-generator[proctitle]` to install this dependancy and enable setting the process name.

Run `totp_generator` with the --help flag for more information.


#### Development
Install the test requirements with `pip install -e .[test]`. Run the tests with pytest.

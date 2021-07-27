#!/usr/bin/env python
"""
Test cli module.
"""
import errno
import json
import os
import sys
import tempfile

import pytest


import mock

from keyrings.alt.file import PlaintextKeyring

import totp_generator
import totp_generator.cli as cli
from totp_generator.core_utils import KeyringTotpGenerator

TEST_FILE = os.path.join('tests', 'test_data.json')
TEST_FILE = os.path.abspath(TEST_FILE)
INVALID_TEST_FILE = os.path.join('tests', 'invalid_data.json')
INVALID_TEST_FILE = os.path.abspath(INVALID_TEST_FILE)


def import_test_data(file=TEST_FILE):
    file_h = open(file, 'r')
    test_data = json.loads(file_h.read())
    return test_data


def cleanup_file(file):
    try:
        os.unlink(file)
    except OSError:
        err = sys.exc_info()[1]
        if err.errno != errno.ENOENT:  # No such file or directory
            raise


class TestTotpUtils:

    def setup_method(self):
        self.PROGNAME = totp_generator.__progname__
        self.VERSION = totp_generator.__version__
        # force keyring to use tmpfile
        PlaintextKeyring.file_path = self.tmp_keyring_file = tempfile.mktemp()
        self.keyring_generator = KeyringTotpGenerator(force_keyring=PlaintextKeyring())
        self.test_data = import_test_data()

    def teardown_method(self):
        # cleanup tmp file
        cleanup_file(self.tmp_keyring_file)
        # reset input
        totp_generator.cli.input = input

    def test_show_version(self):
        correct_out = '{name} version {ver}\n'.format(name=self.PROGNAME, ver=self.VERSION)
        ret_val = cli.version_string()
        assert ret_val == correct_out

    def test_service_menu_no_data(self):
        """Test service menu."""
        with pytest.raises(SystemExit) as wrapped_exit:
            cli.service_menu(self.keyring_generator.get_services())
        assert wrapped_exit.type == SystemExit

    def test_service_menu(self):
        """Test service menu."""
        self.keyring_generator.import_creds_from_file(TEST_FILE)
        with mock.patch('totp_generator.cli.input', lambda x: '1'):
            ret = cli.service_menu(self.keyring_generator.get_services())
        assert ret == 'svc_1'

    def test_service_menu_list(self, capsys):
        """Test service menu."""
        self.keyring_generator.import_creds_from_file(TEST_FILE)
        ret = cli.service_menu(self.keyring_generator.get_services(), list_services=True)
        output = capsys.readouterr()[0]
        assert ret is None
        assert output == "svc_1\nsvc_2\nsvc_3\n"

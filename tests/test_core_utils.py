#!/usr/bin/env python
import errno
import json
import os
import sys
import tempfile

import pyotp
from keyrings.alt.file import PlaintextKeyring

import totp_generator
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
        e = sys.exc_info()[1]
        if e.errno != errno.ENOENT:  # No such file or directory
            raise


class TestTOTPGenerator:
    """Test totp_generator"""

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

    def test_load_creds_no_init(self):
        """Test loading creds without initing an empty data structure."""
        ret = self.keyring_generator.load_creds(init_new=False)
        assert ret is False

    def test_load_creds_new(self):
        """Test loading creds with no existing data."""
        ret = self.keyring_generator.load_creds()
        assert ret == dict()

    def test_load_creds_existing(self):
        """Test loading creds with no existing data."""
        self.keyring_generator.import_creds_from_file(TEST_FILE)
        ret = self.keyring_generator.load_creds()
        assert ret == self.test_data

    def test_import_creds(self):
        """Test import of data and ensure stored data is the same as what we imported."""
        ret = self.keyring_generator.import_creds_from_file(TEST_FILE)
        # when using the file backend the data is stored under the user
        stored_data = json.dumps(self.keyring_generator.creds)
        assert ret is True
        assert json.loads(stored_data) == self.test_data

    def test_import_non_existent_file(self):
        """Test import of data from non-existent file and ensure it fails."""
        res = self.keyring_generator.import_creds_from_file('no-such-file-should-exist')
        assert res is False

    def test_import_invalid_data(self):
        """Test import of data from non-existent file and ensure it fails."""
        res = self.keyring_generator.import_creds_from_file(INVALID_TEST_FILE)
        assert res is False

    def test_export_creds(self):
        """Test export of data and ensure exported data is the same as what we imported."""
        export_file = tempfile.mktemp()
        self.keyring_generator.import_creds_from_file(TEST_FILE)
        self.keyring_generator.export_creds_to_file(export_file)
        file_data = import_test_data(file=export_file)
        cleanup_file(export_file)
        assert file_data == self.test_data

    def test_add_service(self):
        """Test adding a new service."""
        self.keyring_generator.add_service('svc_1', self.test_data['svc_1']['code'])
        stored_data = self.keyring_generator.creds
        assert stored_data == {'svc_1': self.test_data['svc_1']}

    def test_add_service_duplicate(self):
        """Test that adding a duplicate service fails."""
        self.keyring_generator.import_creds_from_file(TEST_FILE)
        ret = self.keyring_generator.add_service('svc_1', self.test_data['svc_1']['code'])
        assert ret is False

    def test_edit_service_no_change(self):
        """Test editing service with no changes."""
        self.keyring_generator.import_creds_from_file(TEST_FILE)
        ret = self.keyring_generator.edit_service('svc_1')
        assert ret is False

    def test_edit_service_name_change_duplicate(self):
        """Test editing service with requesting a duplicate new name."""
        self.keyring_generator.import_creds_from_file(TEST_FILE)
        ret = self.keyring_generator.edit_service('svc_1', new_name='svc_2')
        assert ret is False

    def test_edit_service_name_change(self):
        """Test editing service with requesting a new name."""
        self.keyring_generator.import_creds_from_file(TEST_FILE)
        ret = self.keyring_generator.edit_service('svc_1', new_name='svc_5')
        self.test_data['svc_5'] = self.test_data['svc_1']
        self.test_data.pop('svc_1', None)
        assert ret is True
        assert self.keyring_generator.creds == self.test_data

    def test_edit_service_code_change(self):
        """Test editing service with requesting a code change."""
        self.keyring_generator.import_creds_from_file(TEST_FILE)
        ret = self.keyring_generator.edit_service('svc_1', secret='MFRGGZDFMZTWQ2LP')
        self.test_data['svc_1']['code'] = 'MFRGGZDFMZTWQ2LP'
        assert ret is True
        assert self.keyring_generator.creds == self.test_data

    def test_edit_service_name_code_change(self):
        """Test editing service with requesting a new name and new code."""
        self.keyring_generator.import_creds_from_file(TEST_FILE)
        ret = self.keyring_generator.edit_service('svc_1', new_name='svc_5', secret='MFRGGZDFMZTWQ2LP')
        self.test_data['svc_5'] = self.test_data['svc_1']
        self.test_data['svc_5']['code'] = 'MFRGGZDFMZTWQ2LP'
        self.test_data.pop('svc_1', None)
        assert ret is True
        assert self.keyring_generator.creds == self.test_data

    def test_get_services(self):
        """Test getting services."""
        self.keyring_generator.add_service('svc_1', self.test_data['svc_1']['code'])
        services = self.keyring_generator.get_services()
        assert services == ['svc_1']

    def test_get_totp_code(self):
        """Test generating totp code."""
        self.keyring_generator.import_creds_from_file(TEST_FILE)
        val = self.keyring_generator.get_totp_code('svc_1')
        # force to six digits
        totp = pyotp.TOTP(self.test_data['svc_1']['code'])
        correct_val = "%06d" % (int(totp.now()))
        assert val == correct_val

    def test_re_service(self):
        """Test removing a service."""
        self.keyring_generator.import_creds_from_file(TEST_FILE)
        self.keyring_generator.rm_service('svc_1')
        self.test_data.pop('svc_1', None)
        assert self.keyring_generator.creds == self.test_data


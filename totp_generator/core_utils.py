"""Core functions for Keyring TOTP Generator."""
# ****************************************************************************
# *   Keyring TOTP Generator                                                 *
# *                                                                          *
# *   Copyright (C) 2017 by Jeremy Falling except where noted.               *
# *                                                                          *
# *   This program is free software: you can redistribute it and/or modify   *
# *   it under the terms of the GNU General Public License as published by   *
# *   the Free Software Foundation, either version 3 of the License, or      *
# *   (at your option) any later version.                                    *
# *                                                                          *
# *   This program is distributed in the hope that it will be useful,        *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of         *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
# *   GNU General Public License for more details.                           *
# *                                                                          *
# *   You should have received a copy of the GNU General Public License      *
# *   along with this program.  If not, see <http://www.gnu.org/licenses/>.  *
# ****************************************************************************

import codecs
import json
import logging
from getpass import getuser

import keyring
import onetimepass

import totp_generator

# load logger before keyring to stop log notice on some platforms
logging.basicConfig(level=logging.WARN)
logging.getLogger()
logger = logging.getLogger()

PROGNAME = totp_generator.__progname__
VERSION = totp_generator.__version__
SERVICE_NAME = 'totp_generator'


class KeyringTotpGenerator:

    def __init__(self, force_keyring=None):
        """Return KeyringTotpGenerator object."""
        self.user = getuser()
        if force_keyring:
            keyring.set_keyring(force_keyring)
        self.creds = self.load_creds()

    def load_creds(self, init_new=True):
        """Load TOTP credentials from keyring."""
        keyring_data = keyring.get_password(SERVICE_NAME, self.user)
        if not keyring_data:
            if init_new:
                # keyring does not exist, init a new one.
                return dict()
            else:
                return False

        # data found, parse json
        json_data = json.loads(keyring_data)
        return json_data

    def add_service(self, name, code):
        if name in self.creds:
            logger.error(
                'There is already a service with the name {n}. Use the edit option to update this service.'.format(
                    n=name))
            return False

        self.creds[name] = dict()
        self.creds[name]['code'] = code

        self.save_creds()
        return True

    def edit_service(self, old_name, new_name=None, code=None):
        if new_name in self.creds:
            logger.error(
                'There is already a service with the name {n}.'.format(
                    n=new_name))
            return False

        if not code and not new_name:
            logger.warning('You provided no changes. Leaving service as-is.\n')
            return False

        if code:
            self.creds[old_name]['code'] = code

        if new_name:
            existing_data = self.creds[old_name]
            self.creds.pop(old_name, None)
            self.creds[new_name] = existing_data

        self.save_creds()
        return True

    def export_creds_to_file(self, file_name):
        with open(file_name, 'wb') as f:
            json.dump(self.creds, codecs.getwriter('utf-8')(f), ensure_ascii=False)
        return

    def get_services(self):
        services = []
        for key in sorted(self.creds):
            services.append(key)
        return services

    def get_totp_code(self, service):
        # force six digits
        code = "%06d" % (onetimepass.get_totp(self.creds[service]['code']))
        return code

    def import_creds_from_file(self, file_name):
        try:
            file = open(file_name, 'r')
        except EnvironmentError as e:
            logger.fatal("Error: opening dump file {n}: {e}".format(n=file_name, e=e))
            return False
        try:
            loaded_config = json.loads(file.read())
        except ValueError as err:
            logger.fatal("Error: could not parse dump file. Ensure it is valid json.")
            return False

        self.creds.update(loaded_config)
        self.save_creds()
        return True

    def rm_service(self, service):
        self.creds.pop(service, None)
        self.save_creds()
        return True

    def save_creds(self):
        keyring.set_password(SERVICE_NAME, self.user, json.dumps(self.creds))
        return

"""Core functions for Keyring TOTP Generator."""
# ****************************************************************************
# *   Keyring TOTP Generator                                                 *
# *                                                                          *
# *   Copyright (C) 2017-2022 by Jeremy Falling except where noted.          *
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
from typing import Union

import keyring
import keyring.backend
import pyotp

import totp_generator

# load logger before keyring to stop log notice on some platforms
LOGGER = logging.getLogger(__name__)

PROGNAME = totp_generator.__progname__
VERSION = totp_generator.__version__
SERVICE_NAME = 'totp_generator'


class KeyringTotpGenerator:
    """
    Keyring TOTP Generator Class.
    """

    def __init__(self, force_keyring: keyring.backend.KeyringBackend = None) -> None:
        """
        Init KeyringTotpGenerator object.
        :param force_keyring: Keyring backend object to use. Defaults to
                              None and is auto selected.
        :type force_keyring: keyring.backend.KeyringBackend
        """
        self.user = getuser()
        if force_keyring:
            keyring.set_keyring(force_keyring)
        self.creds = self.load_creds()

    def add_service(self, name: str, secret: str) -> bool:
        """
        Add a new service.
        :param name: Name of service
        :type name: str
        :param secret: Secret service token
        :type secret: str
        :return: True if adding service succeeded, otherwise False.
        :rtype: bool
        """
        if name in self.creds:
            LOGGER.error(
                'There is already a service with the name %s. Use the edit option to update this service.', name)
            return False

        self.creds[name] = dict()
        self.creds[name]['code'] = secret

        self.save_creds()
        return True

    def edit_service(self, old_name: str, new_name: str = None, secret: str = None) -> bool:
        """
        Edit an existing service.
        :param old_name: Current name of the service.
        :type old_name: str
        :param new_name: New name of the service. Do not set to leave
                         unchanged. Defaults to None.
        :type new_name: str
        :param secret:  New secret service token. Do not set to leave
                        unchanged. Defaults to None.
        :type secret: str
        :return: True if updated, otherwise False
        :rtype: bool
        """
        if new_name in self.creds:
            LOGGER.error(
                'There is already a service with the name %s.', new_name)
            return False

        if not secret and not new_name:
            LOGGER.warning('You provided no changes. Leaving service as-is.\n')
            return False

        if secret:
            self.creds[old_name]['code'] = secret

        if new_name:
            existing_data = self.creds[old_name]
            self.creds.pop(old_name, None)
            self.creds[new_name] = existing_data

        self.save_creds()
        return True

    def export_creds_to_file(self, file_name: str) -> bool:
        """
        Export all credentials from the keying to a plain text JSON
        file.
        :param file_name: File name to export data to, optionally
                          including path.
        :type file_name: str
        :return: True
        :rtype: bool
        """
        with open(file_name, 'wb') as file_handle:
            json.dump(self.creds, codecs.getwriter('utf-8')(file_handle), ensure_ascii=False)
        return True

    def get_services(self) -> list:
        """
        Get all service names from keyring.
        :return: All service names
        :rtype: list
        """
        services = []
        for key in sorted(self.creds):
            services.append(key)
        return services

    def get_totp_code(self, service: str) -> str:
        """
        Generate TOTP code for a specific service.
        :param service: Name of service
        :type service: str
        :return: String with six digits
        :rtype: str
        """
        # force six digits
        secret = self.creds[service]['code']
        # force six digits
        totp = pyotp.TOTP(secret)
        code = "%06d" % (int(totp.now()))
        return code

    def import_creds_from_file(self, file_name: str) -> bool:
        """
        Import credentials from file. This will override any existing
        services with the same name.
        :param file_name: File name to import, optionally including
                          path.
        :type file_name: str
        :return: True if import succeeded, otherwise False.
        :rtype: bool
        """
        try:
            file = open(file_name, 'r')
        except EnvironmentError as err:
            LOGGER.fatal("Error: opening dump file %s: %s", file_name, err)
            return False
        try:
            loaded_config = json.loads(file.read())
        except ValueError as err:
            LOGGER.fatal("Error: could not parse dump file. Ensure it is valid json: %s", err)
            return False

        self.creds.update(loaded_config)
        self.save_creds()
        return True

    def load_creds(self, init_new=True) -> Union[bool, dict]:
        """
        Load TOTP credentials from keyring.
        :param init_new:
        :type init_new: bool
        :return: Dict with credential service  data otherwise False
        :rtype: Union[bool, dict]
        """
        # this can throw execptions, but let the caller handle it
        keyring_data = keyring.get_password(SERVICE_NAME, self.user)
        if not keyring_data:
            if init_new:
                # keyring does not exist, init a new one.
                return dict()

            return False

        # data found, parse json
        json_data = json.loads(keyring_data)
        return json_data

    def rm_service(self, service: str) -> bool:
        """
        Remove service by name from services data.
        :param service: Service name
        :type service: str
        :return: True
        :rtype: bool
        """
        self.creds.pop(service, None)
        self.save_creds()
        return True

    def save_creds(self) -> bool:
        """
        Save credentials to keyring.
        :return: True
        :rtype: bool
        """
        keyring.set_password(SERVICE_NAME, self.user, json.dumps(self.creds))
        return True

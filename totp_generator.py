#!/usr/bin/env python3
"""Generate TOTP code. Entries are stored in the keyring."""
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

import argparse
import json
import sys
import signal
import keyring
import onetimepass
from getpass import getuser

PROGNAME = 'Keyring TOTP Generator'
VERSION = '1.0.0'


def signal_handler(signal, frame):
    """Catch interrupts and exit without a stack trace."""
    print('\nExiting...\n')
    sys.exit(0)


def show_version():
    """Show version info and exit."""
    print('{name} version {ver}\n'.format(name=PROGNAME, ver=VERSION))
    sys.exit(0)


def load_creds():
    """Load TOTP crconfeds file from keyring."""
    keyring_data = keyring.get_password("totp_generator", getuser())
    if not keyring_data:
        return dict()

    # data found, parse json
    json_data = json.loads(keyring_data)
    return json_data


def update_creds(totp_creds):
    """Update TOTP conf file in keyring."""
    # update json object in keyring

    keyring.set_password("totp_generator", getuser(), json.dumps(totp_creds))
    print("TOTP object updated")
    return


def add_key():
    """Add element to TOTP conf file in keyring."""
    totp_creds = load_creds()
    name = input("Enter the name of this service: ")
    code = input("Enter the TOTP secret: ")

    if name in totp_creds:
        yes_answers = ['y', 'yes']
        if input("Warning: Entry exists. Do you want to overwrite it? [y/n]: ").lower() not in yes_answers:
            print("Not updating service")
            sys.exit(1)

    # update the creds and exit
    try:
        totp_creds[name]['code'] = code
    except KeyError:
        # service does not exist, add it
        totp_creds[name] = dict()
        totp_creds[name]['code'] = code

    update_creds(totp_creds)
    print()
    sys.exit(0)


def rm_key():
    """Remove element from TOTP conf file in keyring."""
    totp_creds = load_creds()
    service = service_menu(totp_creds)

    totp_creds.pop(service, None)
    update_creds(totp_creds)
    print()
    sys.exit(0)


def edit_key():
    """Add element to TOTP conf file in keyring."""
    totp_creds = load_creds()
    service = service_menu(totp_creds)

    while True:
        name = input("Enter the new name of this service or hit return to leave unchanged: ")

        if name not in totp_creds:
            break

        print('That service name already exists. Please select a new name!\n')

    code = input("Enter the new TOTP secret or hit return to leave unchanged: ")

    if code == '' and name == '':
        print('You provided no changes. Leaving service as-is.\n')
        sys.exit(1)

    if code and code != '':
        totp_creds[service]['code'] = code

    if name and name != '':
        existing_data = totp_creds[service]
        totp_creds.pop(service, None)
        totp_creds[name] = existing_data

    update_creds(totp_creds)
    print()
    sys.exit(0)


def service_menu(totp_creds):
    """Interactive service selection."""
    i = -1
    options = list()

    if len(totp_creds) == 0:
        print('It appears you have not loaded any TOTP data. Please add a TOTP service. Run with --help for more.\n')
        sys.exit(1)

    for key, val in sorted(totp_creds.items()):
        i += 1
        options.append(key)
        print('{i}: {name}'.format(i=i, name=key))

    while True:
        sel = input("\nSelect a service by number: ")
        try:
            # range is exclusive
            if int(sel) in range(0, i + 1):
                break
        except ValueError:
            pass

        print("Your selection is not valid. Try again.")

    return options[int(sel)]


def main():
    """Main function."""
    # catch ctrl+c
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description='TOTP code generator' +
                                                 '\n\nCodes are stored in a keyring supported by the keyring module.' +
                                                 '\nWhen using the below flags, only one can be used at a time.',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-a', '--add', action='store_true', help='add a TOTP service')
    parser.add_argument('-e', '--edit', action='store_true', help='edit a TOTP service')
    parser.add_argument('-r', '--remove', action='store_true', help='remove a TOTP service')
    parser.add_argument('-s', '--service', type=str, default=None, help='specify a TOTP service')
    parser.add_argument('-v', '--version', action='store_true', help='show version and exit')
    args = parser.parse_args()

    # handle flags
    if args.version:
        show_version()

    if args.add:
        add_key()

    if args.remove:
        rm_key()

    if args.edit:
        edit_key()

    # first try to get creds
    totp_creds = load_creds()

    if not args.service:
        service = service_menu(totp_creds)

    else:
        service = args.service
        if service not in totp_creds:
            print('That service does not exist\n')
            sys.exit(1)

    print("%06d" % (onetimepass.get_totp(totp_creds[service]['code'])))


if __name__ == '__main__':
    main()

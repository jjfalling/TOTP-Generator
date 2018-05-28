"""CLI functions for Keyring TOTP Generator."""
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
import binascii
import logging
import signal
import sys

import keyring
import pyperclip

import totp_generator
from totp_generator.core_utils import KeyringTotpGenerator

# Make this optional since installing it may require elevated privileges
try:
    from setproctitle import setproctitle
except ImportError:  # pragma: no cover
    pass

# load logger before keyring to stop log notice on some platforms
logging.basicConfig(level=logging.WARN)
logging.getLogger()
logger = logging.getLogger()

PROGNAME = totp_generator.__progname__
VERSION = totp_generator.__version__
SERVICE_NAME = 'totp_generator'

YES_ANSWERS = ['y', 'yes']

# set the process name before going any further. This allows keychain requests to show as this program instead
# of simply 'python'. Also replace the spaces to work better with some systems.
if 'setproctitle' in sys.modules:
    setproctitle(PROGNAME.replace(' ', '-'))

# backwards compatibility for py2
try:
    input = raw_input
except NameError:
    pass


def signal_handler(signal, frame):  # pragma: no cover
    """Catch interrupts and exit without a stack trace."""
    print('\nExiting...\n')
    sys.exit(0)


def version_string():
    """Show version info and exit."""
    return '{name} version {ver}\n'.format(name=PROGNAME, ver=VERSION)


def service_menu(services):
    """Interactive service selection."""
    i = 0
    options = list()

    if len(services) == 0:
        print(
            'It appears you have not loaded any TOTP data. Please add a TOTP service. Run with --help for more.\n')
        sys.exit(1)

    for service in services:
        i += 1
        options.append(service)
        print('{i}: {name}'.format(i=i, name=service))

    while True:
        user_in = input("\nSelect a service by number: ")
        try:
            sel = int(user_in) - 1
            # range is exclusive
            if int(sel) in range(0, i):
                break
        except ValueError:
            pass

        print("Your selection is not valid. Try again.")

    return options[int(sel)]


def main():
    """Main cli function."""
    # catch ctrl+c
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description=PROGNAME +
                                                 '\n\nUtility that generates TOTP codes and stores the TOTP secrets in ' +
                                                 ' your system keyring.'
                                                 '\nTOTP Secrets are stored in a keyring supported by the keyring ' +
                                                 'module.' +
                                                 '\nWith the exception of the debug flag, only one flag can be used ' +
                                                 'at a time.',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-a', '--add', action='store_true', help='add a TOTP service')
    parser.add_argument('-c', '--copy', action='store_true', help='copy TOTP code to clipboard after generating')
    parser.add_argument('-d', '--debug', action='store_true', help='enable debug logging')
    parser.add_argument('-e', '--edit', action='store_true', help='edit a TOTP service')
    parser.add_argument('--export', dest='export_file', action='store',
                        help='export all credentials to a plain text json file')
    parser.add_argument('--import', dest='import_file', action='store', help='import JSON dump of credentials')
    parser.add_argument('-r', '--remove', action='store_true', help='remove a TOTP service')
    parser.add_argument('-s', '--service', type=str, default=None, help='specify a TOTP service')
    parser.add_argument('-v', '--version', action='store_true', help='show version and exit')
    args = parser.parse_args()

    keyring_generator = KeyringTotpGenerator()

    # handle flags
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if 'setproctitle' not in sys.modules:
        logger.info('setproctitle Module is not loaded. Unable to set process title.')
    logger.debug('keyring module config root: ' + keyring.util.platform_.config_root())
    logger.debug('keyring that will be used: ' + keyring.get_keyring().name)

    if args.version:
        print(version_string())
        sys.exit(0)

    if args.add:
        name = input("Enter the name of this service: ")
        code = input("Enter the TOTP secret: ")
        res = keyring_generator.add_service(name, code)
        if res:
            print("TOTP service added")
        else:
            print("There was an error adding this TOTP service. See above for a detailed error.")
        sys.exit(0)

    if args.remove:
        service = service_menu(keyring_generator.get_services())
        res = keyring_generator.rm_service(service)
        if res:
            print('Removed service {s}\n'.format(s=service))
        else:
            print('Error removing service {s}. See above for more details\n'.format(s=service))
        sys.exit(0)

    if args.edit:
        service = service_menu(keyring_generator.get_services())

        while True:
            name = input("Enter the new name of this service or hit return to leave unchanged: ")
            if not name:
                name = None

            if name not in keyring_generator.get_services():
                break

            print('That service name already exists. Please select a new name!\n')

        code = input("Enter the new TOTP secret or hit return to leave unchanged: ")
        if not code:
            code = None

        ret = keyring_generator.edit_service(service, name, code)
        if ret:
            print("Service {s} updated.".format(s=service))
        else:
            print("Error updating service {s}. See above for a detailed error.".format(s=service))

        sys.exit(0)

    if args.import_file:
        if input("Warning: You are about to import all TOTP credentials from {f}. \nExisting entries that have the\
 same name as imported entries will be overwritten without warning.\nDo you want to continue? [y/n]: ".
                         format(f=args.import_file)).lower() not in YES_ANSWERS:
            print("Not performing import.\n")
            sys.exit(1)

        keyring_generator.import_creds_from_file(args.import_file)
        print("Successfully imported credentials.\n")
        sys.exit(0)

    if args.export_file:
        if input("Warning: You are about to export all TOTP credentials in PLAIN TEXT from your current keying to {f}. \
\nDo you want to continue? [y/n]: ".format(f=args.export_file)).lower() not in YES_ANSWERS:
            print("Not performing export.\n")
            sys.exit(1)

        keyring_generator.export_creds_to_file(args.export_file)
        print("Successfully exported credentials to {n}\n".format(n=args.export_file))
        sys.exit(0)

    if not args.service:
        service = service_menu(keyring_generator.get_services())

    else:
        service = args.service
        if service not in keyring_generator.get_services():
            print('That service does not exist\n')
            sys.exit(1)

    try:
        totp_code = keyring_generator.get_totp_code(service)
        print(totp_code)
        if args.copy:
            pyperclip.copy(totp_code)

        if not args.service:
            print('')

    except TypeError as e:
        print("Error generating TOTP code: {e}\n".format(e=e))
        exit(1)

    except binascii.Error as e:
        if 'Non-base32 digit found' in str(e):
            print("Error generating TOTP code: 'Non-base32 digit found'. Usually this means you did not provide a valid \
TOTP code for the service {s}\n".format(s=service))
        elif 'Incorrect padding' in str(e):
            print("Error generating TOTP code: 'Incorrect padding'. Usually this means you did not provide a valid \
TOTP code for the service {s}\n".format(s=service))
        else:
            print("Error generating TOTP code: {e}\n".format(e=e))
        exit(1)


if __name__ == '__main__':
    main()

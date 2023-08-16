"""CLI functions for Keyring TOTP Generator."""
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

import argparse
import binascii
import logging
import signal
import sys
from typing import Union
import traceback

import keyring
import pyclip

import totp_generator
from totp_generator.core_utils import KeyringTotpGenerator

# Make this optional since installing it may require elevated privileges
try:
    from setproctitle import setproctitle
except ImportError:  # pragma: no cover
    pass

# load logger before keyring to stop log notice on some platforms
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.WARNING)
STDOUT_LOG_HANDLER = logging.StreamHandler()
STDOUT_LOG_HANDLER.setFormatter(logging.Formatter('[%(levelname)-8s] %(message)s'))
LOGGER.addHandler(STDOUT_LOG_HANDLER)

PROGNAME = totp_generator.__progname__
VERSION = totp_generator.__version__
SERVICE_NAME = 'totp_generator'

YES_ANSWERS = ['y', 'yes']

# set the process name before going any further. This allows keychain
# requests to show as this program instead of simply 'python'. Also
# replace the spaces to work better with some systems.
if 'setproctitle' in sys.modules:
    setproctitle(PROGNAME.replace(' ', '-'))


def signal_handler(sig_num, frame):  # pragma: no cover
    # pylint: disable=W0612,W0613
    """
    Catch interrupts and exit without a stack trace. Called by
    signal.signal.
    :param sig_num: Signal number
    :param frame:  The interrupted stack frame
    :return: Never returns, exits with code 0
    :rtype:
    """
    print('\nExiting...\n')
    sys.exit(0)


def version_string() -> str:
    """
    Determine program name version number.
    :return: Program name and version number.
    :rtype: string
    """
    return '{name} version {ver}\n'.format(name=PROGNAME, ver=VERSION)


def service_menu(services: dict, list_services: bool = False, prompt_msg: str = None) -> Union[str, None]:
    """
    Interactive service selection.

    :param services: TOTP services data
    :type services: dict
    :param list_services: Only list services without number and return
                          None. Defaults to False
    :type list_services: bool
    :param prompt_msg: Service prompt message to override default
                       message
    :type prompt_msg: str
    :return: totp service name or None
    :rtype: Union[string, None]
    """
    i = 0
    options = list()

    if len(services) == 0:
        print(
            'It appears you have not loaded any TOTP data. Please add a TOTP service. Run with --help for more.\n')
        sys.exit(1)
    else:
        # get max amount of padding needed
        max_padding = len(str(len(services)))

    for service in services:
        i += 1
        options.append(service)

        if list_services:
            # don't print service number when prompt is disabled
            print(service)
        else:
            # determine service number padding (to improve readability)
            linepad = (max_padding - len(str(i))) * (' ')
            print('{i}: {padding}{name}'.format(i=i, padding=linepad, name=service))

    if list_services:
        return None

    while True:
        if prompt_msg:
            user_in = input("\n" + prompt_msg + ": ")
        else:
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
    # pylint: disable=too-many-branches,too-many-statements
    """
    Main function.
    :return: Does not return, exits with code
    :rtype:
    """
    # catch ctrl+c
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description=PROGNAME + '\n\nUtility that generates TOTP codes and stores the TOTP '
                                                            'secrets in your system keyring.\nTOTP Secrets are stored '
                                                            'in a keyring supported by the keyring module.\n')
    parser.add_argument('-a', '--add', action='store_true', help='add a TOTP service')
    parser.add_argument('-c', '--copy', action='store_true', help='copy TOTP code to clipboard after generating')
    parser.add_argument('-d', '--debug', action='store_true', help='enable debug logging')
    parser.add_argument('-e', '--edit', action='store_true', help='edit a TOTP service')
    parser.add_argument('--export', dest='export_file', action='store',
                        help='export all credentials to a plain text json file')
    parser.add_argument('--import', dest='import_file', action='store', help='import JSON dump of credentials')
    parser.add_argument('-l', '--list', action='store_true', help='list TOTP services')
    parser.add_argument('-r', '--remove', action='store_true', help='remove a TOTP service')
    parser.add_argument('-s', '--service', type=str, default=None, help='specify a TOTP service instead of picking '
                                                                        'from a list.')
    parser.add_argument('-v', '--version', action='store_true', help='show version and exit')
    parser.add_argument('-q', '--quiet', action='store_true', help='does nothing unless combined with another flag:\n '
                                                                   'when used with the copy flag no TOTP code is '
                                                                   'not shown but all other output is shown.\n'
                                                                   'when used with the service flag no output other '
                                                                   'than the TOTP code is shown.\n when used with the'
                                                                   'copy and service flags no output is shown at all.\n'
                                                                   'does not apply to import, export, add, edit, '
                                                                   'remove, debug, and help flags.\n errors will '
                                                                   'always be shown.')
    args = parser.parse_args()

    # handle flags
    if args.debug:
        # set logger level to debug and also include more info in the log string
        LOGGER.setLevel(logging.DEBUG)
        STDOUT_LOG_HANDLER.setFormatter(logging.Formatter('[%(name)s %(levelname)s] %(message)s'))

    if 'setproctitle' not in sys.modules:
        LOGGER.info('setproctitle Module is not loaded. Unable to set process title.')

    try:
        keyring_generator = KeyringTotpGenerator()
    except RuntimeError as err:
        LOGGER.error('Keyring encountered a runtime error: %s', str(err))
        LOGGER.debug('Keyring traceback: ', exc_info=True)
        exit(1)

    LOGGER.debug('keyring module config root: %s', keyring.util.platform_.config_root())
    LOGGER.debug('keyring that will be used: %s', keyring.get_keyring().name)

    if args.version:
        print(version_string())
        sys.exit(0)

    if args.add:
        name = input("Enter the name of this service: ")
        secret = input("Enter the TOTP secret: ")
        res = keyring_generator.add_service(name, secret)
        if res:
            print("TOTP service added")
        else:
            print("There was an error adding this TOTP service. See above for a detailed error.")
        sys.exit(0)

    if args.remove:
        service = service_menu(keyring_generator.get_services(), prompt_msg="Select a service by number to remove")
        res = keyring_generator.rm_service(service)
        if res:
            print('Removed service {s}\n'.format(s=service))
        else:
            print('Error removing service {s}. See above for more details\n'.format(s=service))
        sys.exit(0)

    if args.edit:
        service = service_menu(keyring_generator.get_services(), prompt_msg="Select a service by number to edit")

        while True:
            name = input("Enter the new name of this service or hit return to leave unchanged: ")
            if not name:
                name = None

            if name not in keyring_generator.get_services():
                break

            print('That service name already exists. Please select a new name!\n')

        secret = input("Enter the new TOTP secret or hit return to leave unchanged: ")
        if not secret:
            secret = None

        ret = keyring_generator.edit_service(service, name, secret)
        if ret:
            print("Service {s} updated.".format(s=service))
        else:
            print("Error updating service {s}. See above for a detailed error.".format(s=service))

        sys.exit(0)

    if args.import_file:
        if input("Warning: You are about to import all TOTP credentials from {f}. \nExisting entries that have the "
                 "same name as imported entries will be overwritten without warning.\nDo you want to continue? [y/n]: ".
                 format(f=args.import_file)).lower() not in YES_ANSWERS:
            print("Not performing import.\n")
            sys.exit(1)

        import_res = keyring_generator.import_creds_from_file(args.import_file)
        if import_res:
            print("Successfully imported credentials.\n")
        sys.exit(0)

    if args.export_file:
        if input("Warning: You are about to export all TOTP credentials in PLAIN TEXT from your current keying to {f}."
                 "\nDo you want to continue? [y/n]: ".format(f=args.export_file)).lower() not in YES_ANSWERS:
            print("Not performing export.\n")
            sys.exit(1)

        keyring_generator.export_creds_to_file(args.export_file)
        print("Successfully exported credentials to {n}\n".format(n=args.export_file))
        sys.exit(0)

    if args.list:
        service_menu(keyring_generator.get_services(), list_services=True)
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
        if args.quiet and args.copy:
            pass
        else:
            print(totp_code)

            if not args.service:
                print('')

        if args.copy:
            try:
                pyclip.copy(totp_code)
            except pyclip.base.ClipboardSetupException as err:
                LOGGER.error('Could not setup clipboard. Under Linux, ensure you have xclip installed if running x11 or'
                             ' wl-clipboard if running wayland. See the project readme for more information.')
                LOGGER.debug('pyclip could not seup the clipboard. Full error:', exc_info=True)

    except TypeError as err:
        print("Error generating TOTP code: {e}\n".format(e=err))
        sys.exit(1)

    except binascii.Error as err:
        if 'Non-base32 digit found' in str(err):
            print("Error generating TOTP code: 'Non-base32 digit found'. Usually this means you did not provide a "
                  "valid TOTP code for the service {s}\n".format(s=service))
        elif 'Incorrect padding' in str(err):
            print("Error generating TOTP code: 'Incorrect padding'. Usually this means you did not provide a valid "
                  "TOTP code for the service {s}\n".format(s=service))
        else:
            print("Error generating TOTP code: {e}\n".format(e=err))
        sys.exit(1)


if __name__ == '__main__':
    main()

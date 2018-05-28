import codecs
import os
import sys
from shutil import rmtree

from setuptools import setup, Command

import totp_generator

AUTHOR = 'Jeremy Falling'
DESCRIPTION = 'Utility that generates TOTP codes and stores the TOTP secrets in your system keyring.'
URL = 'https://github.com/jjfalling/totp-generator'

# What packages are required for this module to be executed?
REQUIRED = [
    'keyring>=12.2.0,<13.0.0',
    'keyrings.alt>=3.1,<4.0',
    'onetimepass>=1.0.1,<1.1.0',
    'pyperclip>=1.6.1<1.7.0',
    'setproctitle>=1.1.10,<1.2.0'
]

TESTS_REQUIRED = ["pytest", "pytest-cov", "mock; python_version < '3.4'", "keyrings.alt"]

here = os.path.abspath(os.path.dirname(__file__))

with open("README.md", "r") as fh:
    long_description = fh.read()

def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds...')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution...')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPi via Twine...')
        os.system('twine upload dist/*')

        self.status('Pushing git tags...')
        os.system('git tag {0}'.format(totp_generator.__version__))
        os.system('git push --tags')

        sys.exit()


setup(
    name="TOTP Generator",
    version=totp_generator.__version__,
    author=AUTHOR,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=URL,
    license='GPLv3',
    install_requires=REQUIRED,
    include_package_data=True,
    packages=['totp_generator'],
    entry_points={
        "console_scripts": [
            "totp_generator = totp_generator.cli:main"
        ]
    },
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
    ],
    tests_require=TESTS_REQUIRED,
    extras_require={'test': TESTS_REQUIRED},
    # setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    },
)

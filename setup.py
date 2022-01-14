import codecs
import os
import re
import sys
from shutil import rmtree

from setuptools import Command, setup

import totp_generator

AUTHOR = 'Jeremy Falling'
DESCRIPTION = 'Utility that generates TOTP codes and stores the TOTP secrets in your system keyring.'
URL = 'https://github.com/jjfalling/totp-generator'

# What packages are required for this module to be executed? get this from the reqs file
REQUIRED = [line.rstrip() for line in open(os.path.join(os.path.dirname(__file__), "requirements.txt"))]

TESTS_REQUIRED = ['pytest', 'pytest-cov>2.6', 'mock', 'wheel', 'codecov', 'pylint']

here = os.path.abspath(os.path.dirname(__file__))

with open('README.md', 'r') as fh:
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
    raise RuntimeError('Unable to find version string.')


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
    name='TOTP Generator',
    version=totp_generator.__version__,
    author=AUTHOR,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=URL,
    license='GPLv3',
    install_requires=REQUIRED,
    include_package_data=True,
    packages=['totp_generator'],
    python_requires='>=3.7.0',
    entry_points={
        'console_scripts': [
            'totp_generator = totp_generator.cli:main'
        ]
    },
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
    ],
    tests_require=TESTS_REQUIRED,
    extras_require={
        'dev': ['setuptools', 'twine', 'wheel'],
        'test': TESTS_REQUIRED,
        'proctitle': [line.rstrip() for line in open(os.path.join(os.path.dirname(__file__), "requirements-optional.txt"))]
    },
    # setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    },
)

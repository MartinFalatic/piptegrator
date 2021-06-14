#!/usr/bin/env python

"""

"""

from __future__ import print_function

from os import path
from setuptools import setup
from piptegrator import __config__ as config


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

console_scripts = []
for src_basename in config.CONSOLE_SCRIPTS:
    details = config.CONSOLE_SCRIPTS[src_basename]
    console_scripts.append('{}={}.{}:main'.format(details['scriptname'], details['path'], src_basename))
print(console_scripts)

setup(
    name=config.PKGNAME,
    version=config.VERSION,
    description=config.DESCRIPTION,
    author='Martin F. Falatic',
    author_email='martin@falatic.com',
    copyright='Copyright (c) 2019-2021',
    license='MIT License',
    keywords='pip pip-compile pip-tools requirements git gitlab github pyup',
    url='https://github.com/MartinFalatic/piptegrator',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Development Status :: 5 - Production/Stable',
    ],
    packages=[
        'piptegrator',
    ],
    entry_points={
        'console_scripts': console_scripts,
    },
    install_requires=[
        'configparser;python_version<"3.6"',
        'pip-tools',
        'pygithub',
        'python-gitlab',
        'requests',
    ],
    extras_require={},
    package_data={},
    data_files=[],
    # Derived data
    long_description=long_description,
    long_description_content_type='text/markdown',
)

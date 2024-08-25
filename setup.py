#!/usr/bin/env python

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
    license='MIT License',
    keywords='pip pip-compile pip-tools requirements uv',
    url='https://github.com/MartinFalatic/piptegrator',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Utilities',
    ],
    packages=[
        'piptegrator',
    ],
    entry_points={
        'console_scripts': console_scripts,
    },
    install_requires=[
        'pip-tools',
        'requests',
        'uv',
    ],
    extras_require={},
    package_data={},
    data_files=[],
    # Derived data
    long_description=long_description,
    long_description_content_type='text/markdown',
)

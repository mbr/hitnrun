#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='hitnrun',
    version='0.3dev',
    description='Rerun scons on changed build dependencies.',
    long_description=read('README.rst'),
    author='Marc Brinkmann',
    author_email='git@marcbrinkmann.de',
    url='http://github.com/mbr/hitnrun',
    license='MIT',
    install_requires=['watchdog', 'logbook'],
    entry_points={
        'console_scripts': [
            'hitnrun = hitnrun:main',
        ],
    }
)

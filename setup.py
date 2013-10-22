#!/usr/bin/env python
#-------------------------------------------------------------------
# Filename: setup.py
#  Purpose: Installation script for smsl tool for sending SMS via HTML SMSlink
#   Author: Tom Richter
#    Email: lorchel@gmx.de
#  License: MIT license
#
# Copyright (C) 2012-2013 Tom Richter
#---------------------------------------------------------------------
"""
Tool for sending SMS via HTML SMSlink
=====================================

This is a command line utility for sending short messages with the help of
HTML SMSlink. Currently this is possible with the website smslisto.com.
Now sending a SMS is as far as typing:

send dude "Hey Dude!"
"""

from setuptools import setup
import os
import shutil
import sys


LOCAL_PATH = os.path.abspath(os.path.dirname(__file__))
DOCSTRING = __doc__.split('\n')
# package specific settings
VERSION = '0.0.3'
NAME = 'smsl'
AUTHOR = 'Tom Richter'
AUTHOR_EMAIL = 'lorchel@gmx.de'
LICENSE = 'MIT license'
KEYWORDS = ['send', 'sms', 'mail']
INSTALL_REQUIRES = ['setuptools']
ENTRY_POINTS = {'console_scripts': ['send = smsl:main']}


def convert2to3():
    """
    Convert source to Python 3.x syntax using lib2to3.
    """
    # create a new 2to3 directory for converted source files
    dst_path = os.path.join(LOCAL_PATH, '2to3')
    shutil.rmtree(dst_path, ignore_errors=True)
    # copy original tree into 2to3 folder ignoring some unneeded files

    def ignored_files(adir, filenames):  # @UnusedVariable
        return ['.git', '2to3', 'build', 'dist'] + \
               [fn for fn in filenames if fn.startswith('distribute')] + \
               [fn for fn in filenames if fn.endswith('.egg-info')]
    shutil.copytree(LOCAL_PATH, dst_path, ignore=ignored_files)
    os.chdir(dst_path)
    sys.path.insert(0, dst_path)
    # run lib2to3 script on duplicated source
    from lib2to3.main import main
    print('Converting to Python3 via lib2to3...')
    main('lib2to3.fixes', ['-w', '-n', '--no-diffs', 'smsl.py'])


def setupPackage():
    # use lib2to3 for Python 3.x
    if sys.version_info.major == 3:
        convert2to3()
    # setup package
    setup(
        name=NAME,
        version=VERSION,
        description=DOCSTRING[1],
        long_description=' '.join(DOCSTRING[4:-1]),
        url='',
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        license=LICENSE,
        platforms='OS Independent',
        classifiers=[
            'Environment :: Console',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: SMS'],
        keywords=KEYWORDS,
        install_requires=INSTALL_REQUIRES,
        entry_points=ENTRY_POINTS,
        #use2to3=True,
        py_modules=['smsl'],
    )
    # cleanup after using lib2to3 for Python 3.x
    if sys.version_info.major == 3:
        os.chdir(LOCAL_PATH)


if __name__ == '__main__':
    setupPackage()

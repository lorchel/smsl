#!/usr/bin/env python

from setuptools import setup

VERSION = '0.7'
with open('README.rst') as f:
    README = f.read()
    DESCRIPTION = README.split('\n')[2]
    LONG_DESCRIPTION = '\n'.join(README.split('\n')[5:])

# setup package
setup(name='smsl',
      version=VERSION,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      url='https://github.com/lorchel/smsl',
      author='Tom Richter',
      author_email='lorchel@gmx.de',
      license='MIT',
      platforms='OS Independent',
      keywords=['send', 'sms', 'mail'],
      install_requires=['setuptools'],
      entry_points={'console_scripts': ['send = smsl:main']},
      include_package_data = True,
      py_modules=['smsl']
      )

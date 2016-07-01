SMSL
====
Send command-line SMS via HTML API
----------------------------------

This is a command line utility for sending short messages with the help of
the HTML API of different providers. Now sending a SMS is as far as typing: ::

    send dude "Hey Dude!"

At the first start an example configuration file at the path
``~/.config/smsl.json`` will be created which must be adapted.
You can add profiles, contacts, and a csv file which will additionally
be searched for contacts. All contacts are shared between the profiles.

You need to be registered at a provider which provides the HTML API. The tool
creates a link like ``https://www.x.com/sendsms?user={user}&pw={pw}&to={to}&
from={from}&text={text}`` which will be sent to the provider.

Give your thumb a break! ;)

Requirements
------------
* python 2.7 or python >3.2 and setuptools

Installation
------------
* run ``pip install smsl`` or
* download source and run ``python setup.py install``

Usage
-----
Try ``send -h``.

SMSL
====
Tool for sending SMS via HTML SMSlink
-------------------------------------

This is a command line utility for sending short messages with the help of
HTML SMSlink and different providers. Now sending a SMS is as far as typing: ::

    send dude "Hey Dude!"

Tested providers are: smslisto.com

Please contact the developers to add support for other providers.

At the first start an example configuration file at the path
``~/.config/smsl.cfg`` will be created. Feel free to adapt the file to your needs.
You can add new contacts, new users and a csv file which will additionally
be searched for contacts. All contacts are shared between the users.
You can add your providers username, password and from information, so
that you don't need to enter it every time you want to send a short message.

If you don't want your password to be saved on your harddisk in plain letters
you can comment out this option and enter it each time you send a SMS.
Anyway the created link will include your password in plain letters
and it will be send over your internet connection. This means don't use an
expensive password on your providers account when using this tool.

By the way you need to be registered at your providers website and you need to
have some money on your account. The tool uses the HTML SMSlink service.
The script creates a link like
``https://www.smslisto.com/myaccount/sendsms.php?username=xxx&password=xxx&from=xxx&to=xxx&text=xxx``
and sends it to the provider.

Alternatively, you can use the send_sms function in Python code::

    from smsl import send_sms
    send_sms(url, text, user='test', pw='test', caller='me', to=012, test=False)

Give your thumb a break! ;)


Requirements
------------
* python 2.7 or python >3.2

Installation
------------
* run ``pip install smsl`` or
* download source and run ``python setup.py install``

Usage
-----
Try ``send -h``.

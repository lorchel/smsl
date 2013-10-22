Tool for sending SMS via HTML SMSlink
=====================================

This is a command line utility for sending short messages with the help of
HTML SMSlink. Currently this is possible with the website smslisto.com.
Now sending a SMS is as far as typing:

send dude "Hey Dude!"

At the first start an example configuration file at the path
~/.config/smsl.cfg will be created. Feel free to adapt the file to your needs.
You can add new contacts, new users and a csv file which will additionally
be searched for contacts. All contacts are shared between the users.
You can add your providers username, password and from information, so
that you don't need to enter it every time you want to send a short message.

If you don't want your password to be saved on your harddisk in plain letters
you can comment out this option and indicate it with the command line option
'-p'. Anyway the created link will include your password in plain letters
and it will be send over your internet connection. This means don't use an
expensive password on your providers account when using this tool.

By the way you need to be registered at your providers website and you need to
have some money on your account. The tool uses the HTML SMSlink service.
The script creates a link like
https://www.smslisto.com/myaccount/sendsms.php?username=xxxxxxxxxx&
password=xxxxxxxxxx&from=xxxxxxxxxx&to=xxxxxxxxxx&text=xxxxxxxxxx
and sends it to the provider.

Give your thumb a break! ;)


Requirements
------------
    * python 2.7 or python 3.2

Installation
------------
You have 2 possibilities:
    1. - Download the file smsl.py
       - and run "python smsl.py -h" for usage information
    2. - Clone or download (ZIP button on git website) the repository,
       - install the script with "python setup.py install" (with root privileges)
       - and run "send -h" for usage information.
       - If everything is working you can delete the downloaded files.
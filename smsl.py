#!/usr/bin/env python
#-------------------------------------------------------------------
# Filename: smsl.py
#  Purpose: Client for sending SMS via HTML SMSlink
#   Author: Tom Richter
#    Email: lorchel@gmx.de
#  License: GPLv3
#
# Copyright (C) 2012 Tom Richter
#---------------------------------------------------------------------
"""
Tool for sending SMS via HTML SMSlink
=====================================

This is a command line utility for sending short messages with the help of
HTML SMSlink. Currently this is possible with the website smslisto.com.
Now sending a SMS is as far as typing:

send dude "Hey Dude!"
"""


from HTMLParser import HTMLParser
import ConfigParser
import argparse
import csv
import os.path
import sys
import urllib


CONFIG_FILENAME = os.path.expanduser(os.path.join('~', '.smsl.cfg'))
EPILOG = """
At the first start an example configuration file at the path
%s was created. Feel free to adapt  the file to your needs.
You can add new contacts, new users and a csv file which will additionally
be searched for contacts. All contacts are shared between the users.
You can add your SMSLISTO username, password and from information, so
that you don't need to enter it every time you want to send a short message.

If you don't want your password to be saved on your harddisk in plain letters
you can comment out this option and indicate it with the command line option
'-p'. Anyway the created link will include your password in plain letters
and it will be send over your internet connection. This means don't use an
expensive password on your SMSLISTO account when using this tool. 

By the way you need to be registered at SMSLISTO and you need to have some money
on your account. The tool uses the HTML SMSlink service.
The script creates a link like
https://www.smslisto.com/myaccount/sendsms.php?username=xxxxxxxxxx&
password=xxxxxxxxxx&from=xxxxxxxxxx&to=xxxxxxxxxx&text=xxxxxxxxxx
and sends it to smslisto.com.

Give your thumb a break! ;)
""" % CONFIG_FILENAME

CONFIG_EXAMPLE = """
[Settings]
default_user = example_user
url = https://www.smslisto.com/myaccount/sendsms.php?
country = +1

[Contacts]
dude = +1234567890

[ContactsCSV]
# Uncomment the following rows and add the direct path of your csv file
# if you want to search there for mobile numbers.
# Column names have to be in the first row in this file.
#file = 
#colreceiver = name of receiver
#colnumber = number of receiver

[example_user]
username = Your SMSLISTO username
password = Your SMSLISTO password
from = Your username or your verified phone number
#url = it is possible to set a different url for every user
"""

class SmslError(Exception):
    pass

#http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-
#using-python
class BColors:
    """Colored text in terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

class AnswerSMSLinkParser(HTMLParser):
    """HTMLParser to read answer from server (currently just smslisto.com)"""
    tags = ('result', 'resultstring', 'description', 'partcount', 'endcause')
    def __init__(self):
        HTMLParser.__init__(self)
        self._tag = ''
    def handle_starttag(self, tag, attrs):
        self._tag = tag
        if tag in self.tags:
            setattr(self, tag, '')
    def handle_data(self, data):
        if self._tag in self.tags:
            setattr(self, self._tag, data)
    def handle_endtag(self, tag):
        self._tag = ''

def send_sms(username, password, fromu, to, message, url, test=False):
    """Send SMS with a HTML SMSlink."""
    params = urllib.urlencode({'username': username, 'password': password,
                               'from': fromu, 'to': to,
                               'text': message})
    url = url + params
    if test:
        print('Constructed url:\n%s' % url)
        return url
    else:
        if DEBUG:
            answer = DEBUG_answer
        else:
            url_answer = urllib.urlopen(url)
            answer = url_answer.read()
            url_answer.close()
        parser = AnswerSMSLinkHTMLParser()
        parser.feed(answer)
        parser.close()
        if parser.result == '1':
            print('Answer of server: %s%s %s %s' %
                  (BColors.OKBLUE, parser.resultstring, parser.description,
                   BColors.ENDC))
            return False
        else:
            print('Answer of server: %s%s - %s%s' %
                  (BColors.FAIL, parser.resultstring, parser.description,
                   BColors.ENDC))
            return True

def get_config():
    """Read config from file if possible otherwise create example config file"""
    config = ConfigParser.SafeConfigParser()
    if os.path.exists(CONFIG_FILENAME):
        config.read(CONFIG_FILENAME)
    else:
        with open(CONFIG_FILENAME, 'wb') as f:
            f.write(CONFIG_EXAMPLE.strip('\n'))
    return config

class _NoArgs:
    id = user = pw = fromu = None
    test = False
    
def get_send_args(config, to, message, args=None):
    """Get arguments from config or args and raise SmslError if necessary."""
    if not args:
        args = _NoArgs()
    test = args.test
    if not message:
        raise SmslError('Your message is empty.')
    try:
        default_user = (args.id if args.id else
                        config.get('Settings', 'default_user') if
                        config.has_option('Settings', 'default_user') else None)
        user = args.user if args.user else config.get(default_user, 'username')
        pw = args.pw if args.pw else config.get(default_user, 'password')
        fromu = args.fromu if args.fromu else config.get(default_user, 'from')
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        raise SmslError(
              "All of options 'user', 'pw' and 'fromu' have to exist as "
              "option in the section of default user or have to be defined "
              "as command line option. " +
              ("(current default user: %s)" % default_user if default_user else
               "(no default user)"))
    try:
        url = (config.get(default_user, 'url', raw=True) if
               config.has_option(default_user, 'url') else
               config.get('Settings', 'url', raw=True))
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        raise SmslError('Error when reading url from config file.')

    # Get phone number    
    country = (config.get('Settings', 'country') if
               config.has_option('Settings', 'country') else None)
    def is_phone_number(phone):
        p = phone.translate(None, ' -()')
        return (p.startswith('+') and p[1:].isdigit() or
                p[0] == '0' and p.isdigit() and country)    
    # try to find receiver and number in Contacts
    if not is_phone_number(to) and config.has_option('Contacts', to): 
        to = config.get('Contacts', to)
    # try to find receiver and number in CSV file
    if (not is_phone_number(to) and
            config.has_option('ContactsCSV', 'file') and
            config.has_option('ContactsCSV', 'colreceiver') and
            config.has_option('ContactsCSV', 'colnumber')):
        database = os.path.expanduser(config.get('ContactsCSV', 'file'))
        colreceiver = config.get('ContactsCSV', 'colreceiver').strip()
        colreceiver2 = (config.get('ContactsCSV', 'colreceiver2').strip() if
                        config.has_option('ContactsCSV', 'colreceiver2')
                        else None)
        colnumber = config.get('ContactsCSV', 'colnumber').strip()
        try:            
            with open(database, 'rb') as f:
                reader = csv.DictReader(f, skipinitialspace=True)
                for row in reader:
                    if (row[colreceiver].strip() == to or
                            colreceiver2 and row[colreceiver2].strip() == to):
                        to = row[colnumber]
                        if not is_phone_number(to):
                            raise SmslError('Wrong format of number in CSV col '
                                            '%s.' % colnumber)
                        break
        except IOError:
            raise SmslError('CSV file does not exist at %s.' % database)
        except (csv.Error, KeyError):
            raise SmslError('Error while parsing the CSV file %s.' %
                            database)    
    if not is_phone_number(to):
        raise SmslError('Receiver is no valid phone number or contact not '
                        'found in config file or CSV file.')
    to = to.translate(None, ' -()')
    if to[0] == '0':
        to = to.replace('0', country, 1)
        print('Replace 0 by country code %s.' % country)
    return (user, pw, fromu, to, message, url), dict(test=test)


def main():
    """Get command line arguments and send sms"""
    config = get_config()
    default_user = (config.get('Settings', 'default_user') if
                config.has_option('Settings', 'default_user') else None)
    description = __doc__
    parser = argparse.ArgumentParser(
                        description=description, epilog=EPILOG,
                        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('to',
                        help='Number or contact you wish to send the sms to.')
    parser.add_argument('message', nargs='+',
                        help='The message you want to send. Use quotes! '
                        'Otherwise there will be errors when using *? and '
                        'other special characters.')
    parser.add_argument('-i', '--id', default=default_user,
                        help='Your alias in the config file '
                        '(default: %s)' % default_user if default_user else
                        '(no default)')
    parser.add_argument('-u', '--user',
        help='Your SMSLISTO username')
    parser.add_argument('-p', '--pw',
        help='Your SMSLISTO password')
    parser.add_argument('-f', '--fromu',
        help='Your username or your verified phone number')
    parser.add_argument('-t', '--test', action='store_true',
                        help='Just print url, do not send message. '
                        'You can copy+paste the url into your webbrowser.')
    args = parser.parse_args()
    message = ' '.join(args.message)
    to = args.to
    try:
        args, kwargs = get_send_args(config, to, message, args)
    except SmslError as ex:
        sys.exit(ex)
    send_sms(*args, **kwargs)

DEBUG = False
DEBUG_answer = """
<?xml version="1.0" encoding="utf-8"?> 
<SmsResponse>
        <version>1</version>
        <result>1</result> 
        <resultstring>success</resultstring>
        <description></description>
        <partcount>1</partcount>
        <endcause>fail</endcause>
</SmsResponse>
"""
DEBUG_answer2 = """
<?xml version="1.0" encoding="utf-8"?> 
<SmsResponse>
        <version>1</version>
        <result>0</result> 
        <resultstring>failure</resultstring>
        <description>Invalid number</description>
        <partcount></partcount>
        <endcause>19</endcause>
</SmsResponse>
"""

if __name__ == '__main__':
    main()

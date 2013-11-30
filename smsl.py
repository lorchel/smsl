#!/usr/bin/env python
"""
# SMSL
### Tool for sending SMS via HTML SMSlink

This is a command line utility for sending short messages with the help of
HTML SMSlink and different providers. Now sending a SMS is as far as typing:

    send dude "Hey Dude!"
"""

try:
    import configparser
    from configparser import ConfigParser as ConfigParser
    from html.parser import HTMLParser    
    from urllib.parse import urlencode
    from urllib.request import urlopen    
    TRANS = (str.maketrans(str.maketrans('', '', ' -()')),)
except ImportError:
    import ConfigParser as configparser
    from ConfigParser import SafeConfigParser as ConfigParser
    from HTMLParser import HTMLParser
    from urllib import urlencode, urlopen
    TRANS = (None, ' -()')
import argparse
import csv
import getpass
import os
import sys


CONFIG_FILENAME = os.path.expanduser(os.path.join('~', '.config', 'smsl.cfg'))
CONFIG_FILENAME_ALT = os.path.expanduser(os.path.join('~', '.smsl.cfg'))
EPILOG = """
Supported providers are: smslisto.com
Please contact the developers to add support for other providers.

At the first start an example configuration file at the path
%s will be created. Feel free to adapt the file to your needs.
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
https://www.smslisto.com/myaccount/sendsms.php?username=xxx&password=xxx&
from=xxx&to=xxx&text=xxx
and sends it to the provider.

Give your thumb a break! ;)
""" % CONFIG_FILENAME

CONFIG_EXAMPLE = """
# Commented lines start with a '#'.
# Please edit the file according to your preferences.

[Settings]
default_user = example_user
provider = smslisto
country = +1
#history = ~/.config/smsl_hist.txt # uncomment for history of sent sms

[Contacts]
dude = +1234567890

[ContactsCSV]
# Add the full path to your csv file if you want to search there for mobile
# numbers. Column names have to be in the first row in this file.
#file =
#colreceiver = column header for 'name of receiver' column
#colnumber = column header for 'number of receiver' column

[example_user]
username = Your provider username
#password = Your provider password
from = Your username or your verified phone number
"""


def create_url_smslisto(username, password, from_, to, message):
    url = 'https://www.smslisto.com/myaccount/sendsms.php?'
    params = urlencode({'username': username, 'password': password,
                        'from': from_, 'to': to, 'text': message})
    return url + params

PROVIDERS = {'smslisto': create_url_smslisto}


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

    def replace(self, text):
        for color in [self.HEADER, self.OKBLUE, self.OKGREEN,
                      self.WARNING, self.FAIL, self.ENDC]:
            text = text.replace(color, '')
        return text

bcolors = BColors()


class AnswerSMSLinkHTMLParser(HTMLParser):
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


def send_sms(send_args, provider, test=False):
    """Send SMS with a HTML SMSlink."""
    get_url = PROVIDERS[provider]
    url = get_url(*send_args)
    if test:
        return True, 'Constructed url:\n%s' % url
    elif DEBUG:
        answer = DEBUG_answer
    else:
        url_answer = urlopen(url)
        answer = url_answer.read()
        url_answer.close()
    parser = AnswerSMSLinkHTMLParser()
    parser.feed(answer.decode('utf-8'))
    parser.close()
    succes = parser.result == '1'
    return succes, ('Answer of server: %s%s %s %s' %
                    (bcolors.OKBLUE, parser.resultstring, parser.description,
                     bcolors.ENDC) if succes else
                    'Answer of server: %s%s - %s%s' %
                    (bcolors.FAIL, parser.resultstring, parser.description,
                     bcolors.ENDC))


def get_config():
    """Read config from file or create example config file"""
    config = ConfigParser()
    if not config.read([CONFIG_FILENAME, CONFIG_FILENAME_ALT]):
        dirname = os.path.dirname(CONFIG_FILENAME)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        with open(CONFIG_FILENAME, 'wb') as f:
            f.write(CONFIG_EXAMPLE.strip('\n'))
    return config


def is_phone_number(phone, accept_zero=False):
    """Return if phone is a valid phone number."""
    p = phone.translate(*TRANS)
    return (p.startswith('+') and p[1:].isdigit() or
            p[0] == '0' and p.isdigit() and accept_zero)


def read_csv(config, to=None, country=None):
    if (config.has_option('ContactsCSV', 'file') and
            config.has_option('ContactsCSV', 'colreceiver') and
            config.has_option('ContactsCSV', 'colnumber')):
        database = os.path.expanduser(config.get('ContactsCSV', 'file'))
        colreceiver = config.get('ContactsCSV', 'colreceiver').strip()
        colreceiver2 = (config.get('ContactsCSV', 'colreceiver2').strip() if
                        config.has_option('ContactsCSV', 'colreceiver2')
                        else None)
        colnumber = config.get('ContactsCSV', 'colnumber').strip()
        try:
            with open(database, 'r') as f:
                reader = csv.DictReader(f, skipinitialspace=True)
                if to:
                    for row in reader:
                        if (row[colreceiver].strip().lower() == to.lower() or
                                colreceiver2 and colreceiver2.lower() and
                                row[colreceiver2].strip().lower() == to):
                            to = row[colnumber]
                            if not is_phone_number(to, country):
                                raise SmslError('Wrong format of number in CSV'
                                                ' col %s.' % colnumber)
                            break
                else:
                    to = [(row[colreceiver], row[colnumber])
                          for row in reader if row[colreceiver]]
                    if colreceiver2:
                        to.extend([(row[colreceiver2], row[colnumber])
                                   for row in reader if row[colreceiver2]])
        except IOError:
            raise SmslError('CSV file does not exist at %s.' % database)
        except (csv.Error, KeyError):
            raise SmslError('Error while parsing the CSV file %s.' %
                            database)
    return to


def get_all_contacts(config):
    return sorted((list(config.items('Contacts'))
                   if config.has_section('Contacts') else []) +
                  read_csv(config) or [])


def get_send_args(config, to, message, test=False, default_user=None):
    """Get arguments from config or args and raise SmslError if necessary."""
    if not message:
        raise SmslError('Your message is empty.')
    if not default_user and not config.has_option('Settings', 'default_user'):
        raise SmslError("The user has to be given as argument with -i "
                        "or has to be defined "
                        "in the config file as option default_user in section "
                        "Settings.")
    default_user = default_user or config.get('Settings', 'default_user')

    def get_option(option, raw=False):
        try:
            return (config.get(default_user, option, raw=raw) if
                    config.has_option(default_user, option) else
                    config.get('Settings', option, raw=raw))
        except (configparser.NoSectionError, configparser.NoOptionError):
            raise SmslError('Error when reading %s from config file.' % option)
    user = get_option('username')
    from_ = get_option('from')
    provider = get_option('provider')
    if provider not in PROVIDERS:
        raise SmslError('Unknown provider: %s' % provider)
    # Get phone number
    country = get_option('country')
    # Try to find receiver and number in Contacts and csv file
    if not is_phone_number(to, country) and config.has_option('Contacts', to):
        to = config.get('Contacts', to)
    if not is_phone_number(to, country):
        to = read_csv(config, to, country)
    if not is_phone_number(to, country):
        raise SmslError('Receiver is no valid phone number or contact not '
                        'found in config file or CSV file.')
    to = to.translate(*TRANS)
    msg = ''
    if to[0] == '0':
        to = to.replace('0', country, 1)
        msg = 'Replace 0 by country code %s.' % country
    try:
        pw = get_option('password')
    except SmslError:
        pw = getpass.getpass('Please enter your provider password: ')
    return (user, pw, from_, to, message), provider, dict(test=test), msg


def main():
    """Get command line arguments and send sms"""
    config = get_config()
    default_user = (config.get('Settings', 'default_user') if
                    config.has_option('Settings', 'default_user') else None)
    description = __doc__
    parser = argparse.ArgumentParser(
        description=description, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('to', nargs='?',
                        help='Number or contact you wish to send the sms to.')
    parser.add_argument('message', nargs='*',
                        help='The message you want to send. Use quotes! '
                        'Otherwise there will be errors when using *? and '
                        'other special characters.')
    parser.add_argument('-i', '--id', default=default_user,
                        help='Your alias in the config file '
                        '(default: %s)' % default_user if default_user else
                        '(no default)')
    parser.add_argument('-t', '--test', action='store_true',
                        help='Just print url, do not send message. '
                        'You can copy+paste the url into your webbrowser.')
    parser.add_argument('-c', '--count', action='store_true',
                        help='Count characters in message, do not send.')
    parser.add_argument('-s', '--show', action='store_true',
                        help='Show all available contacts.')
    args = parser.parse_args()
    message = ' '.join(args.message)
    if args.count:
        N = len(message)
        print('The message has %d characters. These are %d sms with 160 (145) '
              'characters' % (N, 1 if N <= 160 else (N - 160 - 1) // 145 + 2))
        return
    if args.show:
        contacts = get_all_contacts(config)
        if contacts:
            print('%30s %s' % ('contact', 'number'))
            print('%30s %s' % ('-' * 10, '-' * 10))
            for (name, number) in contacts:
                print('%30s %s' % (name, number))
        else:
            print('No contacts found.')
        return
    try:
        send_args, provider, send_kwargs, msg = get_send_args(
            config, args.to, message, args.test, args.id)
        if msg:
            print(msg)
    except SmslError as ex:
        sys.exit(ex)
    result, answer = send_sms(send_args, provider, **send_kwargs)
    print(answer)
    if (not DEBUG and not args.test and
            config.has_option('Settings', 'history')):
        fname = os.path.expanduser(config.get('Settings', 'history'))
        with open(fname, 'a') as f:
            f.write("user: %s receiver: %s msg: '%s' response: %s\n" %
                    (args.id, args.to, message, bcolors.replace(answer)))

DEBUG = False
DEBUG_answer = b"""
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
DEBUG_answer2 = b"""
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

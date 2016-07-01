#!/usr/bin/env python
"""
# SMSL
### Send command-line SMS via HTML API

This is a command line utility for sending short messages with the help of
the HTML API of different providers. Now sending a SMS is as far as typing:

    send dude "Hey Dude!"
"""

import argparse
import csv
import json
import os
import re

try:
    from urllib.request import urlopen
    TRANS = (str.maketrans(str.maketrans('', '', ' -()')),)
except ImportError:
    from urllib import urlopen
    TRANS = (None, ' -()')

CONFIG = os.path.expanduser(os.path.join('~', '.config', 'smsl.json'))
EPILOG = """
At the first start an example configuration file at the path
%s will be created which must be adapted.
You can add profiles, contacts, and a csv file which will additionally
be searched for contacts. All contacts are shared between the profiles.

You need to be registered at a provider which provides the HTML API. The tool
creates a link like https://www.x.com/sendsms?user={user}&pw={pw}&to={to}&
from={from}&text={text} which will be sent to the provider.

Give your thumb a break! ;)
""" % CONFIG

CONFIG_EXAMPLE = """
# Comments start with #.
# Please edit the file according to your preferences.

{
"default_profile": "example",

#"contacts": {
#    "dude": "+1234567890"
#    },

#"contacts_csv": {
#    "file": "example.csv",
#    "colreceiver": "name",  # column name for receiver names
#    "colnumber": "mobile"   # column name for mobile number
#    },

"example": {
    # url for HHTP request of provider SMS gateway, {} fields are replaced by the corresponding variables,
    # must contain mandatory {to} and {text} fields
    "url": "https://www.x.com/sendsms?user={user}&pw={pw}&to={to}&from={from}&text={text}",
#    "print_answer": true,  # print answer from server
#    "history": null,       # write history of all sent sms in this file
#    "country_code": null,  # replace leading zero with country code, e.g. "+1"
    # default parameters for {} fields in url, can be changed from command line
    "user": "your_username",
    "pw": "your_password",
    "from": "your_phone_number"
    }
}
"""


class SmslError(Exception):
    pass


class ConfigJSONDecoder(json.JSONDecoder):
    """Strip lines from comments."""

    def decode(self, s):
        s = '\n'.join(l.split('#', 1)[0] for l in s.split('\n'))
        return super(ConfigJSONDecoder, self).decode(s)


def read_config(fname):
    if not os.path.exists(fname):
        dirname = os.path.dirname(fname)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        with open(fname, 'wb') as f:
            f.write(CONFIG_EXAMPLE.strip('\n'))
    try:
        with open(fname) as f:
            return json.load(f, cls=ConfigJSONDecoder)
    except ValueError as ex:
        raise SmslError('Error while parsing the configuration: %s' % ex)


def get_contacts(config):
    contacts = config.get('contacts', {})
    try:
        subconf = config['contacts_csv']
        database = os.path.expanduser(subconf['file'])
        colreceiver = subconf['colreceiver'].strip()
        colreceiver2 = subconf.get('colreceiver2', '').strip()
        colnumber = subconf['colnumber'].strip()
    except KeyError:
        return contacts
    try:
        with open(database, 'r') as f:
            reader = csv.DictReader(f, skipinitialspace=True)
            contacts2 = {row[colreceiver]: row[colnumber]
                         for row in reader if row[colreceiver]}
            contacts2.update(contacts)
            if colreceiver2:
                contacts2.update({row[colreceiver2]: row[colnumber]
                                  for row in reader if row[colreceiver2]})
            return contacts2
    except IOError:
        raise SmslError('CSV file does not exist at %s.' % database)
    except (csv.Error, KeyError):
        raise SmslError('Error while parsing the CSV file %s.' %
                        database)


def transform_number(number, contacts, country_code=None):
    onumber = number
    number = number.translate(*TRANS)
    if number in contacts:
        number = contacts[number]
    if number.startswith('0') and country_code is not None:
        number = number.replace('0', country_code, 1)
    if not (number.startswith('+') and number[1:].isdigit() or
            number.isdigit()):
        raise SmslError('%s is not a valid phone number' % onumber)
    return number


def send_sms(url, text, to, test=False, **kwargs):
    """Send SMS with a HTML SMSlink."""
    url = url.format(text=text, to=to, **kwargs)
    if test:
        answer = 'Constructed url: %s' % url
    else:
        url_answer = urlopen(url)
        answer = url_answer.read()
        url_answer.close()
    return answer


def main():
    """Get command line arguments read config and send sms"""
    config = read_config(CONFIG)
    default_profile = config.get('default_profile')
    description = __doc__
    parser = argparse.ArgumentParser(
        description=description, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    msg = 'Number or contact you wish to send the sms to.'
    parser.add_argument('to', nargs='?', help=msg)
    msg = ('The message text you want to send. Use quotes! Otherwise there '
           'will be errors when using *? and other special characters.')
    parser.add_argument('text', nargs='*', help=msg)
    msg = 'Select the profile'
    if default_profile is not None:
        msg = msg + ' (default: %s)' % default_profile
    msg = msg + '.'
    parser.add_argument('-p', '--profile', default=default_profile, help=msg)
    parser.add_argument('-o', '--options', action='store_true',
                        help='Show availlable options for profile.')
    parser.add_argument('-t', '--test', action='store_true',
                        help='Just print url, do not send message. '
                        'You can copy+paste the url into your webbrowser.')
    parser.add_argument('-c', '--count', action='store_true',
                        help='Count characters in message, do not send.')
    parser.add_argument('-s', '--show', action='store_true',
                        help='Show all available contacts.')

    args, remaining_args = parser.parse_known_args()
    text = ' '.join(args.text)
    if args.count:
        N = len(text)
        print('The message has %d characters. These are %d sms with 160 (145) '
              'characters' % (N, 1 if N <= 160 else (N - 160 - 1) // 145 + 2))
        return
    if args.show:
        contacts = get_contacts(config)
        if contacts:
            print('%30s %s' % ('contact', 'number'))
            print('%30s %s' % ('-' * 10, '-' * 10))
            for (name, number) in sorted(contacts.items()):
                print('%30s %s' % (name, number))
        else:
            print('No contacts found.')
        return
    prof = config[args.profile]
    url = prof['url']
    msg = ('additional arguments according to url in selected profile\n'
           'url: %s' % url)
    parser2 = argparse.ArgumentParser(usage=msg, add_help=False)
    for option in re.findall('\{(.*?)\}', url):
        if option in ('to', 'text'):
            continue
        msg = ('defaults to %s' % prof[option] if option in prof else
               'mandatory argument')
        parser2.add_argument('--' + option, default=prof.get(option), help=msg)
    if args.options:
        parser2.print_help()
        return
    contacts = get_contacts(config)
    numbers = [transform_number(n, contacts, prof.get('country_code'))
               for n in args.to.split(',')]
    to = ','.join(numbers)
    options = parser2.parse_args(remaining_args)
    answer = send_sms(url, text, to, test=args.text, **vars(options))
    if prof.get('print_answer', True) or args.test:
        print(answer)
    if not args.test and prof.get('history'):
        log_msg = ("profile: %s receiver: %s msg: '%s' response: %s\n" %
                   (args.profile, to, text, answer))
        fname = os.path.expanduser(prof['history'])
        with open(fname, 'a') as f:
            f.write(log_msg)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
#-------------------------------------------------------------------
# Filename: setup.py
#  Purpose: Client for sending SMS with smslisto.com
#   Author: Tom Richter
#    Email: lorchel@gmx.de
#  License: GPLv3
#
# Copyright (C) 2012 Tom Richter
#---------------------------------------------------------------------
"""
Tool for sending SMS with smslisto.com
======================================

This is a command line utility for sending short messages with the help of
the website smslisto.com. Now sending a SMS is as far as typing:

send dude "Hey Dude!"
"""


from HTMLParser import HTMLParser
import ConfigParser
import argparse
import csv
import os.path
import sys
import urllib


DEBUG = False
CONFIG_FILENAME = os.path.expanduser(os.path.join('~', '.smsl.cfg'))
SMSLISTO_URL = 'https://www.smslisto.com/myaccount/sendsms.php?%s'
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


#http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-
#using-python
class BColors:
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

class AnswerSMSLISTOHTMLParser(HTMLParser):
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

def send_sms(username, password, fromu, to, message, test=False):
    params = urllib.urlencode({'username': username, 'password': password,
                           'from': fromu, 'to': to,
                           'text': message})
    url = SMSLISTO_URL % params
    if test:
        print('Constructed url:\n % s' % url)
    else:
        if DEBUG:
            answer = DEBUG_answer
        else:
            url_answer = urllib.urlopen(url)
            answer = url_answer.read()
            url_answer.close()
        parser = AnswerSMSLISTOHTMLParser()
        parser.feed(answer)
        parser.close()
        if parser.result == '1':
            print('Answer of server: %s%s %s %s' %
                  (BColors.OKBLUE, parser.resultstring, parser.description,
                   BColors.ENDC))
        else:
            print('Answer of server: %s%s - %s%s' %
                  (BColors.FAIL, parser.resultstring, parser.description,
                   BColors.ENDC))

def get_config():
    config = ConfigParser.SafeConfigParser()
    if os.path.exists(CONFIG_FILENAME):
        config.read(CONFIG_FILENAME)
    else: # create example config file     
        config.add_section('Settings')
        config.set('Settings', 'default_user', 'example_user')
        config.add_section('Contacts')
        config.set('Contacts', 'example_contact', '+number_of_example_contact')
        config.add_section('ContactsCSV')
        config.set('ContactsCSV', '#file', 'Uncomment and add here the direct '
                   'path of your csv file if you want to search there for '
                   'mobile numbers. '
                   'Field names have to be in the first row')
        config.set('ContactsCSV', '#fieldreceiver', 'Field name of the column '
                   'with the name of the receivers.')
        config.set('ContactsCSV', '#fieldnumber', 'Field name of the column '
                   'with the mobile numbers.')
        config.add_section('example_user')
        config.set('example_user', '#username', 'Uncomment this section to not '
                   'state your SMSLISTO username every time you send a sms.')
        config.set('example_user', '#password', 'Your SMSLISTO password')
        config.set('example_user', '#from', 'Your username or your verified '
                   'phone number')
        with open(CONFIG_FILENAME, 'wb') as configfile:
            config.write(configfile)
    return config

def main():
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
    default_user = args.id
    try:
        user = args.user if args.user else config.get(default_user, 'username')
        pw = args.pw if args.pw else config.get(default_user, 'password')
        fromu = args.fromu if args.fromu else config.get(default_user, 'from')
    except ConfigParser.NoSectionError:
        sys.exit('Config file has no section [%s].' % default_user)
    except ConfigParser.NoOptionError:
        sys.exit("All of options 'user', 'pw' and 'fromu' have to exist as "
                 "option in section "
                 "[%s] in config file or as command line option." %
                 default_user)
    to = (config.get('Contacts', args.to).translate(None, ' -()') if
          config.has_option('Contacts', args.to) else args.to)
    if not to.startswith('+') or not to[1:].isdigit():
        # try to find receiver and number in CSV file
        try:
            database = os.path.expanduser(config.get('ContactsCSV', 'file'))
            fieldreceiver = config.get('ContactsCSV', 'fieldreceiver').strip()
            fieldnumber = config.get('ContactsCSV', 'fieldnumber').strip()
            with open(database, 'rb') as f:
                reader = csv.DictReader(f, skipinitialspace=True)
                for row in reader:
                    if row[fieldreceiver].strip() == to:
                        to = row[fieldnumber].translate(None, ' -()')
                        if not to.startswith('+') or not to[1:].isdigit():
                            sys.exit('Wrong format of number in CSV field %s.' %
                                     fieldnumber)
                        break
        except ConfigParser.NoSectionError as ex:
            if ex.option.endwith('CSV'):
                sys.exit("Maybe you have a typo in your config file. Section "
                         "[%s] does not exist." % ex.section)
        except ConfigParser.NoOptionError as ex:
            if ex.option != 'file':
                sys.exit("Maybe you have a typo in your config file. Section "
                         "[%s] option '%s' does not exist." % (ex.section,
                                                               ex.option))
        except IOError:
            sys.exit('CSV Database does not exist %s.' % database)
        except (csv.Error, KeyError):
            sys.exit('Error while parsing the CSV database %s.' % database)
    if not to.startswith('+') or not to[1:].isdigit():
        sys.exit('Receiver is no valid mobile number or contact not found '
                 'in config file or database.')
    message = ' '.join(args.message)
    if not message:
        sys.exit('Your message is empty.')
    send_sms(user, pw, fromu, to, message, test=args.test)


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

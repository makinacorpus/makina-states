#!/usr/bin/env python3
from __future__ import absolute_import, division, print_function
# -*- coding: utf-8 -*-
# GNU GPL v3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

# https://github.com/regilero/check_pop3_cleaner
# check_pop3_cleaner: connects a pop3 account and optionnaly deletes emails

import sys
import os
import argparse
import time
import datetime
import poplib
import traceback


def xstr(s):
    return ''if s is None else str(s)

class CheckPop3Cleaner(object):

    def __init__(self):
        self._program = "check_pop3_cleaner"
        self._version = "1.0"
        self._author = "Régis Leroy (regilero)"
        self._nick = "POP3"
        self._ok = 0
        self._warning = 1
        self._critical = 2
        self._unknown = 3
        self._pending = 4
        self.args = None
        self.debug = False

    def get_stats(self, human=False):
        if human:
            return 'Size: {0} - {1} message(s)'.format(
                self.sizeof_fmt(self.mbox_size),
                self.num_messages)
        else:
            # 'label'=value[UOM];[warn];[crit];[min];[max]
            return 'size={0};{1};{2};;{2}; messages={3};{4};{5};;{5};'.format(
                self.mbox_size,
                xstr(self.warn_thresold_size),
                xstr(self.crit_thresold_size),
                self.num_messages,
                xstr(self.warn_thresold_num),
                xstr(self.crit_thresold_num),)

    def critical(self, msg):
        print('{0} CRITICAL - {1} | {2}'.format(self._nick,
                                                msg,
                                                self.get_stats()))
        sys.exit(self._critical)

    def warning(self, msg):
        print('{0} WARNING - {1} | {2}'.format(self._nick,
                                               msg,
                                               self.get_stats()))
        sys.exit(self._warning)

    def unknown(self, msg):
        print('{0} UNKNOWN - {1} | {2}'.format(self._nick,
                                               msg,
                                               self.get_stats()))
        sys.exit(self._unknown)

    def ok(self, msg):
        print('{0} OK - {1} | {2}'.format(self._nick,
                                          msg,
                                          self.get_stats()))
        sys.exit(self._ok)

    def opt_parser(self):
        """Parse arguments"""
        self.num_messages = 0
        self.mbox_size = 0
        self.warn_thresold_size = 0
        self.warn_thresold_num = 0
        self.crit_thresold_size = 0
        self.crit_thresold_num = 0

        parser = argparse.ArgumentParser(
            prog=self._program,
            formatter_class=argparse.RawTextHelpFormatter,
            description=("Connect a POP3 account, check mailbox size, number"
                " of messages and may also\ndelete some of theses messages."),
            epilog=("Note that if you activate the delete part the number of "
                    "messages are taken\nbefore the delete operation.\n"
                    " Examples:\n"
                    "    ./check_pop3_cleaner.py  -H imap.example.com -D"
                    " -u foo@example.com \n      -p \"iskJHjsyHNpopmlkT2IKUDj\""
                    " -t 10 --delete=10 -w 524288,\n       -c 1048576,2000\n"
                    "    ./check_pop3_cleaner.py  -H imap.example.com -D"
                    " -u bar \n      -p \"ams25IUqsnBD25dd4\""
                    " -d 25 -t 10 -w 262144,50 -c 524288,100\n"
                    "    ./check_pop3_cleaner.py  -H imap.example.com -D"
                    " -u bar \n      -p \"ams25IUqsnBD25dd4\""
                    " -d 25 -t 10 -w , -c ,\n"))
        parser.add_argument('-v', '--version',
                            version='%(prog)s {0}'.format(self._version),
                            action='version', help='show program version')
        parser.add_argument('-H', '--hostname', required=True, nargs='?',
                            help=('hostname (directory name for burp) '
                                  '[default: %(default)s]'))
        parser.add_argument('-u', '--user', required=True, nargs='?',
                            help='User account to log in ')
        parser.add_argument('-p', '--password', required=True, nargs='?',
                            help='User account password')
        parser.add_argument('-d', '--delete', default=0, nargs='?', type=int,
                            help=('How many messages should we delete?'
                            "[default: %(default)s].\nUseful for test accounts"))
        parser.add_argument('-s', '--ssl', default=False,
                            action='store_true',
                            help=('If true connect using SSL/TLS'))
        parser.add_argument('-a', '--apop', default=False,
                            action='store_true',
                            help=('If true connect using APOP protocol'))
        parser.add_argument('-P', '--port', default=110, type=int,
                            nargs='?',
                            help=(('POP3 port [default: %(default)s] '
                                   'use 995 for ssl')))
        parser.add_argument('-t', '--timeout', default=15, nargs='?', type=int,
                            help=('Timeout [default: %(default)s]'))
        parser.add_argument('-D', '--debug',
                            action='store_true', help=('Debug Mode'))
        parser.add_argument('-w', '--warning', default='1048576,200',
                            const='1048576,200', nargs='?',
                            help=("Warning thresolds pair,\n  * first value is "
                              "maximum size of mbox in octets,\n"
                              "  * second value is maximum number of messages\n"
                              "    in this mbox.\nUse empty values around the"
                              " coma to remove a check\nfor size or number"
                              " [default: %(default)s]"))
        parser.add_argument('-c', '--critical', default='10485760,1000',
                            const='10485760,1000', nargs='?',
                            help=("Critical thresolds pair,\n  * first value is "
                              "maximum size of mbox in octets,\n"
                              "  * second value is maximum number of messages\n"
                              "    in this mbox.\nUse empty values around the"
                              " coma to remove a check\nfor size or number"
                              " [default: %(default)s]"))

        self.args = vars(parser.parse_args())

        if self.args['debug']:
            self.debug = True
            print("DEBUG argparse: {0!r}".format(self.args))

        self.parse_thresolds()

    def parse_thresolds(self):
        """"Parse thresolds arguments."""
        thresolds = self.args['warning'].split(',')
        if len(thresolds) != 2:
            self.critical('Invalid format for warning thresolds: "{0}"'.format(
                self.args['warning']))
        try:
            self.warn_thresold_size = None if not thresolds[0] else int(thresolds[0])
            self.warn_thresold_num = None if not thresolds[1] else int(thresolds[1])
        except ValueError:
            self.critical(('Invalid format for warning thresolds,'
                           ' something is not an int there: "{0}"').format(
                               self.args['warning']))
        thresolds = self.args['critical'].split(',')
        if len(thresolds) != 2:
            self.critical('Invalid format for critical thresolds: "{0}"'.format(
                self.args['critical']))
        try:
            self.crit_thresold_size = None if not thresolds[0] else int(thresolds[0])
            self.crit_thresold_num = None if not thresolds[1] else int(thresolds[1])
        except ValueError:
            self.critical(('Invalid format for critical thresolds,'
                           ' something is not an int there : "{0}"').format(
                               self.args['critical']))

        if self.debug:
            print ("DEBUG thresolds: [size = w:{0} c:{1}] "
                   "[number = w:{2} c:{3}]").format(
                self.warn_thresold_size,
                self.crit_thresold_size,
                self.warn_thresold_num,
                self.crit_thresold_num)

        if (self.warn_thresold_size is not None
          and self.crit_thresold_size is not None
          and self.warn_thresold_size >= self.crit_thresold_size):
            self.unknown(('Warning thresold ({0}) should be lower than the '
                          'critical one ({1})').format(self.warn_thresold_size,
                                                       self.crit_thresold_size))
        if (self.warn_thresold_num is not None
          and self.crit_thresold_num is not None
          and self.warn_thresold_num >= self.crit_thresold_num):
            self.unknown(('Warning thresold ({0}) should be lower than the '
                          'critical one ({1})').format(self.warn_thresold_num,
                                                       self.crit_thresold_num))

    def sizeof_fmt(self,num):
        """output helper, from http://stackoverflow.com/a/1094933/550618

        transform an octet number if KB/MB/GB, etc
        """
        if num is None:
          return ''
        for x in ['bytes','KB','MB','GB','TB']:
            if num < 1024.0:
                return "%3.1f %s" % (num, x)
            num /= 1024.0

    def get_connection(self):
        """Return a POP3 connection object"""
        try:
            if self.args['ssl']:
                # TODO, handle opt args keyfile/certfile
                conn = poplib.POP3_SSL(host=self.args['hostname'],
                                            port=self.args['port'],
                                            timeout=self.args['timeout'])
            else:
                conn = poplib.POP3(host=self.args['hostname'],
                                        port=self.args['port'],
                                        timeout=self.args['timeout'])
        except (Exception,) as e:
            self.critical('Error while establish POP3 connection: {0}'.format(e))

        try:
            if self.debug:
                conn.set_debuglevel(2)
            return conn

        except (Exception,) as e:
            self.force_end_conn(conn)
            self.critical('Early error on POP3 connection: {0}'.format(e))

    def force_end_conn(self,conn):
        """Use it to close connection on any aborting code"""
        if self.debug:
            print("we had a problem, force POP3 session end")
        conn.quit()

    def login(self, conn):
        """Manage POP3 session user login"""
        try:
            welcome = conn.getwelcome()
            if self.debug:
                print("Welcome receveid: {0}".format(welcome))
            if self.args['apop']:
                msg = conn.apop(self.args['user'],self.args['password'])
                if self.debug:
                    print(msg)
            else:
                msg = conn.user(self.args['user'])
                if self.debug:
                    print(msg)
                msg = conn.pass_(self.args['password'])
                if self.debug:
                    print(msg)
        except (Exception,) as e:
            self.force_end_conn(conn)
            self.critical('Error on login: {0}'.format(e))

    def manage_messages(self, conn):
        """Get number of messages in account and optionnaly delete some."""
        try:
            infos = conn.stat()
            self.mbox_size = infos[1]
            if self.debug:
                print('Size of mbox: {0}'.format(self.sizeof_fmt(self.mbox_size)))
            mlist = [a for a in conn.list()]
            self.num_messages = len(mlist[1])
            if self.debug:
                print('Number of messages: {0}'.format(self.num_messages))
                print('Protocol message: {0}'.format(mlist[0]))
            if not mlist[0].decode().startswith('+OK') :
                self.critical('Error on LIST response: {0}'.format(mlist[0].decode()))
            if self.args['delete']:
                cpt = 0
                for maildef in mlist[1]:
                    if cpt >= self.args['delete']:
                        break
                    msgnum = int(maildef.decode().split(' ')[0])
                    if self.debug:
                        print("Deleteting message number {0}".format(msgnum))
                    conn.dele(msgnum)
                    cpt = cpt+1

        except (Exception,) as e:
            trace = traceback.format_exc()
            self.force_end_conn(conn)
            self.critical('Error on messages management: {0}{1}'.format(e, trace))

    def test_thresolds(self):
        """Check thresolds of number of messages and size of mbox"""
        warn_num = crit_num = warn_size = crit_size = False
        if self.warn_thresold_size != '':
            if self.mbox_size >= self.warn_thresold_size:
                if self.mbox_size >= self.crit_thresold_size:
                    crit_size = True
                else:
                    warn_size = True
        else:
            if self.crit_thresold_size is not None:
                if self.mbox_size >= self.crit_thresold_size:
                    crit_size = True

        if self.warn_thresold_num is not None:
            if self.num_messages >= self.warn_thresold_num:
                if self.num_messages >= self.crit_thresold_num:
                    crit_num = True
                else:
                    warn_num = True
        if self.crit_thresold_num is not None:
            if self.num_messages >= self.crit_thresold_num:
                crit_num = True

        if crit_num :
            if crit_size:
                self.critical(('Size of mailbox is too high: '
                   '{0}>={1} and number of messages is too high: '
                   '{2}>={3}').format(self.sizeof_fmt(self.mbox_size),
                                      self.sizeof_fmt(self.crit_thresold_size),
                                      self.num_messages,
                                      self.crit_thresold_num))
            else:
                # Only report the critical one
                self.critical(('Number of messages is too high: '
                   '{0}>={1}').format(self.num_messages,
                                      self.crit_thresold_num))
        if crit_size:
            # Only report the critical one
            self.critical(('Size of mailbox is too high: '
               '{0}>={1}').format(self.sizeof_fmt(self.mbox_size),
                                  self.sizeof_fmt(self.crit_thresold_size)))
        if warn_size:
            if warn_num:
               self.warning(('Size of mailbox is high: '
                   '{0}>={1} and number of messages is high also: '
                   '{2}>={3}').format(self.sizeof_fmt(self.mbox_size),
                                      self.sizeof_fmt(self.warn_thresold_size),
                                      self.num_messages,
                                      self.warn_thresold_num))
            else:
                self.warning(('Size of mailbox is high: '
                   '{0}>={1}').format(self.sizeof_fmt(self.mbox_size),
                                      self.sizeof_fmt(self.warn_thresold_size)))
        if warn_num:
            self.warning(('Number of messages is high: '
                  '{0}>={1}').format(self.num_messages,
                                     self.warn_thresold_num))


    def pop_session(self):
        """Manage a full POP3 session open/do things/close"""
        conn = self.get_connection()
        self.login(conn)
        self.manage_messages(conn)
        if self.debug:
            print("Closing")
        conn.quit()

    def run(self):
        """Main, parse args, launch the pop3 session, check results"""
        self.opt_parser()
        self.pop_session()
        self.test_thresolds()
        self.ok(self.get_stats(True))


def main():
#    try:
        check_pop3 = CheckPop3Cleaner()
        check_pop3.run()
#    except Exception, e:
#        print 'Unknown error UNKNOW - {0}'.format(e)
#        sys.exit(3)


if __name__ == "__main__":
    main()


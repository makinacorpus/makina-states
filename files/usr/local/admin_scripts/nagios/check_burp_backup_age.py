#!/usr/bin/python
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

# https://github.com/regilero/check_burp_backup_age
# check_burp_backup_age: Local check, Check freshness of last backup for
# a given host name.

import sys
import os
import argparse
import time
import datetime


class CheckBurp(object):

    def __init__(self):
        self._program = "check_burp_backup_age"
        self._version = "0.1"
        self._author = "Régis Leroy (regilero)"
        self._nick = "BURP"
        self._ok = 0
        self._warning = 1
        self._critical = 2
        self._unknown = 3
        self._pending = 4
        self.args = None
        self.diff_min = None

    def critical(self, msg):
        print '{0} CRITICAL - {1}'.format(self._nick, msg)
        sys.exit(self._critical)

    def warning(self, msg):
        print '{0} WARNING - {1}'.format(self._nick, msg)
        sys.exit(self._warning)

    def unknown(self, msg):
        print '{0} UNKNOWN - {1}'.format(self._nick, msg)
        sys.exit(self._unknown)

    def ok(self, msg):
        print '{0} OK - {1}'.format(self._nick, msg)
        sys.exit(self._ok)

    def opt_parser(self):
        parser = argparse.ArgumentParser(
            prog=self._program,
            description=("Local check, Check freshness of last backup for a "
                         "given host name.\n\nRunning on the backup server "
                         "this program will check the timestamp file of the "
                         "last backup for a given host and get the age of this"
                         " last successful run. This age is then compared to "
                         "thresolds to generate alerts."),
            epilog=("Note that this is a local check, running on the backup "
                    "server.\nSo the hostname argument is not used to perform"
                    " any distant connection.\n"))
        parser.add_argument('-v', '--version',
                            version='%(prog)s {0}'.format(self._version),
                            action='version', help='show program version')
        parser.add_argument('-H', '--hostname', required=True, nargs='?',
                            help=('hostname (directory name for burp) '
                                  '[default: %(default)s]'))
        parser.add_argument('-d', '--directory', default='/backups', nargs='?',
                            help=('base directory path for backups (where are '
                                  'the backups?) [default: %(default)s]'))
        parser.add_argument('-w', '--warning', default=1560, const=1560,
                            type=int, nargs='?',
                            help=('Warning thresold, time in minutes before '
                                  'going to warning [default: %(default)s]'))
        parser.add_argument('-c', '--critical', default=1800, const=1800,
                            type=int, nargs='?',
                            help=('Critical thresold, time in minutes before '
                                  'going to critical [default: %(default)s]'))

        self.args = vars(parser.parse_args())

        if self.args['warning'] >= self.args['critical']:
            self.unknown(('Warning thresold ({0}) should be lower than the '
                          'critical one ({1})').format(self.args['warning'],
                                                       self.args['critical']))

        self.bckpdir = self.args['directory'] + '/' + self.args['hostname']
        self.bckpdircur = self.bckpdir + '/current'
        self.ftimestamp = self.bckpdircur + '/timestamp'

    def test_backup_dirs(self):
        if not os.path.isdir(self.args['directory']):
            self.critical(('Base backup directory {0}'
                           ' does not exists').format(self.args['directory']))
        if not os.path.isdir(self.bckpdir):
            self.critical(('Host backup directory {0}'
                           ' does not exists').format(self.bckpdir))
        if not os.path.isdir(self.bckpdircur):
            self.critical(('Current Host backup directory {0}'
                           ' does not exists').format(self.bckpdircur))

    def read_backup_timestamp(self):
        if not os.path.isfile(self.ftimestamp):
            self.critical(('timestamp file '
                           'does not exists ({0})').format(self.ftimestamp))
        lines = []
        with open(self.ftimestamp) as f:
            lines = f.readlines()

        if not len(lines):
            self.critical(('timestamp file seems'
                           ' to be empty ({0})').format(self.ftimestamp))

        tline = lines.pop()
        parts = tline.split()
        if len(parts) not in [3, 4]:
            self.critical(('invalid syntax in '
                           'timestamp file ({0})').format(self.ftimestamp))

        btime = time.strptime(parts[1] + ' ' + parts[2], "%Y-%m-%d %H:%M:%S")
        btime = datetime.datetime(*btime[:6])
        ctime = time.localtime()
        ctime = datetime.datetime(*ctime[:6])
        diff = ctime-btime
        self.diff_min = int((diff.seconds + (diff.days * 24 * 3600))/60)
        self.diff_human = ('{0} day(s) {1:02d} hour(s) {2:02d} '
                           'minute(s)').format(diff.days,
                                               diff.seconds//3600,
                                               (diff.seconds//60) % 60)

    def test_thresolds(self):
        if self.diff_min >= self.args['warning']:
            if self.diff_min >= self.args['critical']:
                self.critical(('Last backup is too old: '
                               '{0} ({1}>={2})').format(self.diff_human,
                                                        self.diff_min,
                                                        self.args['critical']))
            else:
                self.warning(('Last backup starts to get old: '
                              '{0} ({1}>={2})').format(self.diff_human,
                                                       self.diff_min,
                                                       self.args['warning']))
        else:
            self.ok(('Last backup is fresh enough: '
                     '{0} ({1}<{2})').format(self.diff_human,
                                             self.diff_min,
                                             self.args['warning']))

    def run(self):
        self.opt_parser()

        self.test_backup_dirs()
        self.read_backup_timestamp()
        self.test_thresolds()
        self.unknown('No exit made before end of check, this is not normal.')


def main():
    try:
        check_burp = CheckBurp()
        check_burp.run()
    except Exception, e:
        print 'Unknown error UNKNOW - {0}'.format(e)
        sys.exit(3)


if __name__ == "__main__":
    main()

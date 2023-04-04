#!/bin/sh
# --
# Checks supervisorctl for programs that are not in the state of RUNNING.
# That is to say STOPPED, STARTING, BACKOFF, STOPPING, EXITED, FATAL, UNKNOWN
#
#
# @author: Steve Lippert | steve.lippert@gmail.com | Management Research Services, Inc.
# @version: 0.1
# @date: 2011/03/03 (YMD)
# --
#   Copyright Steve Lippert 2011
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#



# --------------------------------------------------------------------
# configuration
# --------------------------------------------------------------------
PROGNAME="$(basename $0)"
CWD="${PWD}"
cd "$(dirname $0)"
W="${PWD}"
cd "${CWD}"
ERR_MESG=()
export PATH="/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin"
if [ -e /usr/lib/nagios/plugins/utils.sh ];then
    LIBEXEC="/usr/lib/nagios/plugins"
else
    LIBEXEC="${W}"
fi
. $LIBEXEC/utils.sh
SUPERVISORCTL=$1

# --------------------------------------------------------------------


# --------------------------------------------------------------------
# functions
# --------------------------------------------------------------------

function print_help() {
	echo ""
	echo "Checks supervisorctl to see if all programs are running."
	echo ""
	echo "This plugin is NOT developped by the Nagios Plugin group."
	echo "Please do not e-mail them for support on this plugin, since"
	echo "they won't know what you're talking about."
	echo ""
	echo "For contact info, read the plugin itself..."
}
function check_supervisor(){
	check_command=$(${SUPERVISORCTL} status | grep -E '(STOPPED)|(STARTING)|(BACKOFF)|(STOPPING)|(EXITED)|(FATAL)|(UNKNOWN)' | wc -l)
	if (( $check_command != 0 )); then
		echo "One or more of your programs are not running!"
		exit $STATE_CRITICAL
	else
		echo "OK: All of your programs are running!"
		exit $STATE_OK
	fi
}

# --------------------------------------------------------------------
# startup checks
# --------------------------------------------------------------------

if [ $# -eq 1 ]; then
	check_supervisor
fi

while [ "$1" != "" ]
do
	case "$1" in
		--help) print_help; exit $STATE_OK;;
		-h) print_help; exit $STATE_OK;;
	esac
done

#!/bin/sh

##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with check_bacula.pl.  If not, see <http://www.gnu.org/licenses/>.

# ===============
# check_postqueue - plugin to chech the length of postfix queue
# ===============
# * written by Silver Salonen, Estonia

# version 1.0.2 (16.Apr.2010)
# * bugfix: "NOT_" was still used - the change was done only in usage

# version 1.0.1 (28.Apr.2008)
# * replace ! with "NOT_" in as a negating command

# version 1.0 (21.Apr.2008)
# plugin return codes:
# 0	OK
# 1	Warning
# 2	Critical
# 3	Unknown

while getopts "hvw:c:f:" opt
do
	case $opt in
		h)
			showhelp=1
			break
		;;
		w)
			warning="$OPTARG"
		;;
		c)
			critical="$OPTARG"
		;;
		f)
			from="$OPTARG"
		;;
		v)
			verbose=1
		;;
	esac
done

postqueue="`which postqueue 2>/dev/null`"
if [ ! "$postqueue" ]; then
	echo "Could not find postqueue!"
	exit 3
fi

printUsage() {
	echo "Usage: $0 [-h] [-v] -w <warning> -c <critical> [ -f <[!]from-address>]"
	echo ""
	echo "Example: $0 -w 50 -c 100 -f '!MAILER-DAEMON'"
}

printHelp() {
	printUsage
	echo ""
	echo "This plugin checks the number of messages in Postfix queue."
	echo "You may specify <from-address> to include messages only from the specific address or negate the result with '!', ie. '!<from-address>'."
	echo ""
	echo "For more details, see inside the script ;)"
	echo ""
	exit 3
}

getQueue () {
	queue="`$postqueue -p | grep "^[A-Z0-9]" | grep -v "Mail queue is empty"`"
	if [ "$from" ]; then
		# $from begins with '!', so negate
		if ( echo "$from" | grep '^!' > /dev/null ); then
			from="-v `echo "$from" | sed 's/^!//'`"
		fi
		queue=`echo "$queue" | grep -i $from`
	fi
	if [ ! "$queue" ]; then
		echo 0
	else
		echo "$queue" | wc -l | sed "s/^ *//"
	fi
}

if [ "$showhelp" = "1" ]; then
	printHelp
	exit 3
fi

if [ ! "$warning" ] || [ ! "$critical" ]; then
	printUsage
	exit 3
fi

if [ $warning -ge $critical ]; then
	echo "<warning> has to be smaller than <critical>!"
	exit 3
fi

queue=`getQueue`

echo "Number of queued messages: $queue"

if [ "$queue" -ge "$critical" ]; then
	exit 2
elif [ "$queue" -ge "$warning" ]; then
	exit 1
else
	exit 0
fi

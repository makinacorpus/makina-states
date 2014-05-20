#!/bin/bash
recipient='sysadmin@makina-corpus.com'
if /usr/sbin/sas2ircu-status | grep -q Okay
then
echo 'RAID status is okay'
else
echo -e 'RAID check failed' | mailx -s "RAID check on $HOSTNAME failed" $recipient
fi


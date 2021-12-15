#!/usr/bin/env bash
if [[ -z $USEREMAIL ]];then exit 0;fi
/usr/bin/printf '%b' "
***** Monitoring Alert: $NOTIFICATIONTYPE\n *****\n
Host: $HOSTDISPLAYNAME / $HOSTNAME\n
Status: $HOSTSTATE\n
IP: $HOSTADDRESS\n
IcingaWeb: $ICINGAWEB\n
Informations:\n
--------------\n
$HOSTOUTPUT\n
\n
Date/H: $LONGDATETIME"\
| /usr/bin/mail -s \
"** MonitoringAlert ** ${HOSTDISPLAYNAME}/${HOSTADDRESS}: ${HOSTSTATE} - ${NOTIFICATIONTYPE} **" \
"$USEREMAIL"
# vim:set et sts=4 ts=4 tw=80:

#!/usr/bin/env bash
if [[ -z $USEREMAIL ]];then exit 0;fi
/usr/bin/printf '%b' "
***** Monitoring Alert: $NOTIFICATIONTYPE *****\n
Service: $SERVICENAME\n
Status: $SERVICESTATE\n
Host: $HOSTNAME\n
IP: $HOSTADDRESS\n
Date/H: $LONGDATETIME\n
IcingaWeb: $ICINGAWEB\n
Informations:\n
--------------\n
$SERVICEOUTPUT\n"\
| /usr/bin/mail -s \
"** MonitoringAlert ** $HOSTDISPLAYNAME: $SERVICENAME/$SERVICESTATE - $NOTIFICATIONTYPE **" \
"$USEREMAIL"
# vim:set et sts=4 ts=4 tw=80:

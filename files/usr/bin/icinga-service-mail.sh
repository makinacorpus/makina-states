#!/usr/bin/env bash
/usr/bin/printf '%b' \
"***** Monitoring Alert: $NOTIFICATIONTYPE *****\n"
"Service: $SERVICENAME\n"\
"Status: $SERVICESTATE\n"\
"Host: $HOST.NAME\n"\
"IP: $HOSTADDRESS\n"\
"Date/H: $LONG_DATE_TIME\n"\
"Informations:\n"\
"--------------\n"\
"$SERVICEOUTPUT\n"\
| /usr/bin/mail -s\
"** MonitoringAlert ** $HOSTDISPLAYNAME: $service.name$/$service.state$ - $NOTIFICATIONTYPE **"\
"$USEREMAIL"
# vim:set et sts=4 ts=4 tw=80:

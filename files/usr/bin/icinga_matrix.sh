#!/usr/bin/env bash
echo "$@">>/tmp/matrix
# Matrix items:
MX_TOKEN=${MX_TOKEN:-$1}
MX_SERVER=${MX_SERVER:-$2}
MX_ROOM=${MX_ROOM:-$3}
MX_TYPE=${MX_TYPE:-${4:-host}}

if [[ -z $MX_ROOM ]];then echo no room;exit 0;fi
if [[ -z $MX_SERVER ]];then echo no server;exit 0;fi
if [[ -z $MX_TOKEN ]];then echo no token;exit 0;fi

MX_TXN="`date "+%s"`$(( RANDOM % 9999 ))"

warn_ico="⚠"
error_ico="🟥 "
ok_ico="🟩"
question_ic="❓"

#Set the message icon based on service state
# For nagios, replace  with NAGIOS_ to get the environment variables from Nagios
if [ "$HOSTSTATE" = "UP" ]
then
    ICON=$ok_ico
elif [ "$HOSTSTATE" = "DOWN" ]
then
    ICON=$error_ico
fi

if [ "$SERVICESTATE" = "UNKNOWN" ]
then
    ICON=$question_ico
elif [ "$SERVICESTATE" = "OK" ]
then
    ICON=$ok_ico
elif [ "$SERVICESTATE" = "WARNING" ]
then
    ICON=$warn_ico
elif [ "$SERVICESTATE" = "CRITICAL" ]
then
    ICON=$error_ico
fi

#MY_HOSTNAME=`hostname`
#read message
#while read line; do
#  message="${message}\n${line}"
#done

HOST_BODY="@room MonitoringAlert: ${ICON-} ${HOSTDISPLAYNAME}/${HOSTADDRESS}: ${HOSTSTATE} - ${NOTIFICATIONTYPE}"
SERVICE_BODY="@room MonitoringAlert: ${ICON-} $HOSTDISPLAYNAME: $SERVICENAME/$SERVICESTATE - ${NOTIFICATIONTYPE}"

case $MX_TYPE in
    host) BODY=$HOST_BODY;;
    service) BODY=$SERVICE_BODY;;
    *) BODY=$HOST_BODY;;
esac

# Post into maint room
curl -XPOST --header 'Content-Type: application/json' --header 'Accept: application/json' -d "{
  \"msgtype\": \"m.text\",
  \"body\": \"$BODY\"
}" "$MX_SERVER/_matrix/client/r0/rooms/$MX_ROOM/send/m.room.message?access_token=$MX_TOKEN"
# vim:set et sts=4 ts=4 tw=80:

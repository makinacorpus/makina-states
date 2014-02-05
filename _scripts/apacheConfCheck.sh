#!/bin/bash
# Generate json output for salt around apache2 -t syntax checker managment
echo "{"

# Load apache envvars
. /etc/apache2/envvars
# Deactivate modules
/usr/sbin/apache2 -t 2>&1 |grep -q "Syntax OK"
if [[ "$?" = "0" ]]; then
  echo '"changed":"false",'
  echo '"comment":"Apache2 configuration files syntax OK"'
  EXIT=0
else
  # Changes detected
  echo '"changed":"true",'
  echo '"comment":"Apache2 configuration syntax errors detected"'
  OUT=$(/usr/sbin/apache2 -t 2>&1)
  echo ',"command_output":"'${OUT//\"/\\\"}'"'
  EXIT=1
fi;
echo "}"
exit $EXIT

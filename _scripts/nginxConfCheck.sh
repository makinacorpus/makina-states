#!/bin/bash
# Generate json output for salt around nginx -t syntax checker managment
echo "{"

/usr/sbin/nginx -t 2>&1 |grep -q "test is successful"
if [[ "$?" = "0" ]]; then
  echo '"changed":"false",'
  echo '"comment":"nginx configuration files syntax OK"'
  EXIT=0
else
  # Changes detected
  echo '"changed":"true",'
  echo '"comment":"nginx configuration syntax errors detected"'
  OUT=$(/usr/sbin/nginx -t 2>&1)
  echo ',"command_output":"'${OUT}'"'
  EXIT=1
fi;
echo "}"
exit $EXIT

#!/usr/bin/env bash
if [ "x$1" = "x" ];then
./test.sh > log
fi
sed -re  "s/^ +.*(\[DEBUG   \])/\1/g"  log |grep CLOUD_TIMER > timing

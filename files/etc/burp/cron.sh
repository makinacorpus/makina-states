#!/usr/bin/env bash
# small wrapper to switch over the rigth python
set -e
if [ -x "$(which python2.7 2>/dev/null)" ];then
    python=python2.7
elif [ -x "$(which python2.6 2>/dev/null)" ];then
    python=python2.6
else
    python="python"
fi
python="$(which $python)"
if [ ! -x "${python}" ];then echo "nopython";exit 1;fi
ver=$("${python}" -c "import sys;print sys.version[0:3]")
for i in 2.4 2.5;do
    if [ "x${ver}" = "x${i}" ];then echo "python too old";exit 2;fi
done
"${python}" "/etc/burp/cron.py"
# vim:set et sts=4 ts=4 tw=0:

#!/usr/bin/env bash
cd $(dirname $0)/..
bootstrap="makina-states.services.bootstrap"
if [[ -n $1 ]];then
    bootstrap="${bootstrap}_${1}"
fi
i_prereq() {
    apt-get install -y build-essential m4 libtool pkg-config autoconf gettext bzip2 groff man-db automake libsigc++-2.0-dev tcl8.5 git python-dev swig libssl-dev libzmq-dev
}
die_in_error() {
    ret=$?
    if [[ $ret != 0 ]];then
        exit $ret
    fi 
}
i_prereq || die_in_error
mark="/srv/salt/makina-states/.sbootstrapped"
if [[ $? == 0 ]];then
    if [[ -f $mark ]];then
        echo "already done";
        exit 0;
    fi
    ps aux|egrep "salt-(master|minion|syndic)" |awk '{print $2}'|xargs kill -9
    cd /srv/salt/makina-states
    python bootstrap.py \
    && bin/buildout -N\
    && /srv/salt/makina-states/bin/salt-call --local state.sls $bootstrap\
    && sleep 2 && salt-key -A -y
    ret=$?
    if [[ $ret == 0 ]];then
        touch $mark
        echo "changed=yes comment='salt installed in $1'"
     else
        exit $ret
    fi
else
    exit $?
fi
# vim:set et sts=4 ts=4 tw=80:

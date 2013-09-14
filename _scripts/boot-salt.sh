#!/usr/bin/env bash
MASTERSALT="${MASTERSALT:-mastersalt.makina-corpus.net}"
MASTERSALT_PORT="${MASTERSALT_PORT:-4506}"
if [[ -z $SALT_BOOT ]];then
    SALT_BOOT="$1"
fi
cd $(dirname $0)/..
bootstrap="makina-states.services.bootstrap"
if [[ -n $SALT_BOOT ]];then
    bootstrap="${bootstrap}_${SALT_BOOT}"
fi
i_prereq() {
    apt-get update && apt-get install -y build-essential m4 libtool pkg-config autoconf gettext bzip2 groff man-db automake libsigc++-2.0-dev tcl8.5 git python-dev swig libssl-dev libzmq-dev
}
die_in_error() {
    ret=$?
    if [[ $ret != 0 ]];then
        exit $ret
    fi
}
mark="/srv/salt/makina-states/.sbootstrapped"
if [[ -f $mark ]];then
    echo "already done";
    exit 0;
fi
if [[ $? == 0 ]];then
i_prereq || die_in_error
if [[ $SALT_BOOT == "mastersalt" ]];then
    if [[ ! -f /srv/pillar/salt.sls ]];then
cat > /srv/pillar/salt.sls << EOF
salt:
  minion:
    master: 127.0.0.1
    interface: 127.0.0.1
  master:
    interface: 127.0.0.1

mastersalt-minion:
  master: ${MASTERSALT}
  master_port: ${MASTERSALT_PORT}
EOF
    fi
    if [[ ! -f /srv/pillar/top.sls ]];then
cat > /srv/pillar/top.sls << EOF
base:
  '*':
    - salt
EOF
    fi
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
        echo "changed=yes comment='salt installed'"
     else
        exit $ret
    fi
else
    exit $?
fi
# vim:set et sts=5 ts=4 tw=80:

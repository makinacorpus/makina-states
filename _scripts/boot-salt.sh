#!/usr/bin/env bash
MASTERSALT="${MASTERSALT:-mastersalt.makina-corpus.net}"
MASTERSALT_PORT="${MASTERSALT_PORT:-4506}"
PILLAR=${PILLAR:-/srv/salt}
ROOT=${ROOT:-/srv/salt}
MS=$ROOT/makina-states
STATES_URL="https://github.com/makinacorpus/makina-states.git"
PROJECT_URL="${PROJECT_URL:-}"
PROJECT_BRANCH="${PROJECT_BRANCH:-salt}"
PROJECT_TOPSTATE="${PROJECT_TOPSTATE:-state.highstate}"
if [[ -z $SALT_BOOT ]];then
    SALT_BOOT="$1"
fi
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
for i in "$PILLAR" "$ROOT";do
    if [[ ! -d $i ]];then
        mkdir -pv $i
    fi
done
if [[ -f $mark ]];then
    echo "already done";
    exit 0;
fi
i_prereq || die_in_error
if [[ ! -d "$MS/.git" ]];then
    git clone "$STATES_URL" "$MS"
    ret=$?
    if [[ $ret != 0 ]];then
        echo "Failed to download makina-states"
        exit -1
    fi
fi
cd $MS
if [[ ! -f .boot_bootstrap ]];then
    python bootstrap.py
    ret=$?
    if [[ $ret != "0" ]];then
        echo "Failed bootstrap"
        exit -1
    fi
    touch .boot_bootstrap
fi
if [[ ! -f .boot_buildout ]];then
    bin/buildout
    ret=$?
    if [[ $ret != "0" ]];then
        echo "Failed buildout"
        exit -1
    fi
    touch .boot_buildout
fi
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
cd /
ps aux|egrep "salt-(master|minion|syndic)" |awk '{print $2}'|xargs kill -9
/srv/salt/makina-states/bin/salt-call --local state.sls $bootstrap\
&& sleep 2 && salt-key -A -y
ret=$?
if [[ $ret == 0 ]];then
    touch $mark
    echo "changed=yes comment='salt installed'"
 else
    exit $ret
fi
if [[ -n $PROJECT_URL ]];then
    BR=""
    if [[ -n $PROJECT_BRANCH ]];then
        BR="-b $PROJECT_BRANCH"
    fi
    git clone $BR "$PROJECT_URL" "$ROOT/project"
    ret=$?
    if [[ $ret != 0 ]];then
        echo "Failed to download project from $PROJECT_URL"
        exit -1
    fi
    rsync -azv "$ROOT/project" "$ROOT/"
    salt-call $PROJECT_TOPSTATE
fi
# vim:set et sts=5 ts=4 tw=80:

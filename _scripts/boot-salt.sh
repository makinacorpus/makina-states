#!/usr/bin/env bash
#
# SEE MAKINA-STATES DOCS FOR FURTHER INSTRUCTIONS:
#
#    - https://github.com/makinacorpus/makina-states
#
# BOOTSTRAP SALT ON A BARE UBUNTU MACHINE FOR RUNNING MAKINA-STATES
# - install prerequisites
# - configure pillar for salt and maybe mastersalt
# - bootstrap salt
# - maybe bootstrap a salt base project
#
#
# Toubleshooting:
# - If the script fails, just relaunch it and it will continue where it was
# - You can safely relaunch it
#

if [[ -f /etc/lsb-release ]];then
    . /etc/lsb-release
fi
base_packages=""
base_packages="$base_packages build-essential m4 libtool pkg-config autoconf gettext bzip2"
base_packages="$base_packages groff man-db automake libsigc++-2.0-dev tcl8.5 python-dev"
base_packages="$base_packages swig libssl-dev libyaml-dev debconf-utils python-virtualenv libzmq3-dev"
base_packages="$base_packages vim git"
UBUNTU_NEXT_RELEASE="saucy"
CHRONO="$(date "+%F_%H-%M-%S")"

export PATH=/srv/salt/makina-states/bin:$PATH
MASTERSALT="${MASTERSALT:-mastersalt.makina-corpus.net}"
MASTERSALT_PORT="${MASTERSALT_PORT:-4506}"
PILLAR=${PILLAR:-/srv/pillar}
ROOT=${ROOT:-/srv/salt}
MS=$ROOT/makina-states
STATES_URL="https://github.com/makinacorpus/makina-states.git"
PROJECT_URL="${PROJECT_URL:-}"
PROJECT_BRANCH="${PROJECT_BRANCH:-salt}"
PROJECT_TOPSTATE="${PROJECT_TOPSTATE:-state.highstate}"
PROJECT_SETUPSTATE="${PROJECT_SETUPSTATE}"
if [[ -z $SALT_BOOT ]];then
    SALT_BOOT="$1"
fi
bootstrap="makina-states.services.bootstrap"
if [[ -n $SALT_BOOT ]];then
    bootstrap="${bootstrap}_${SALT_BOOT}"
fi

i_prereq() {
    to_install=""
    if [[ $(dpkg-query -s python-software-properties 2>/dev/null|egrep "^Status:"|grep installed|wc -l)  == "0" ]];then
        apt-get install -y --force-yes python-software-properties
    fi
    # XXX: only lts package in this ppa
    if     [[ "$(dpkg-query -s libzmq3     2>/dev/null|egrep "^Status:"|grep installed|wc -l)"  == "0" ]] \
        || [[ "$(dpkg-query -s libzmq3-dev 2>/dev/null|egrep "^Status:"|grep installed|wc -l)"  == "0" ]];\
        then
        echo " [bs] Installing ZeroMQ3"
        cp  /etc/apt/sources.list /etc/apt/sources.list.$CHRONO.sav
        sed -re "s/${DISTRIB_CODENAME}/${UBUNTU_NEXT_RELEASE}/g" -i /etc/apt/sources.list
        apt-get remove -y --force-yes libzmq libzmq1 libzmq-dev &> /dev/null
        apt-get update -qq && apt-get install -y --force-yes libzmq3-dev
        ret=$?
        sed -re "s/${UBUNTU_NEXT_RELEASE}/${DISTRIB_CODENAME}/g" -i /etc/apt/sources.list
        apt-get update
        if [[ $ret != "0" ]];then
            die $ret "Install of zmq3 failed"
        fi
    fi
    for i in $base_packages;do
        if [[ $(dpkg-query -s $i 2>/dev/null|egrep "^Status:"|grep installed|wc -l)  == "0" ]];then
            to_install="$to_install $i"
        fi
    done
    if [[ -n $to_install ]];then
        echo " [bs] Installing pre requisites: $to_install"
        echo 'changed="yes" comment="prerequisites installed"'
        apt-get update && apt-get install -y --force-yes $to_install
    fi
}
die() {
    ret=$1
    shift
    echo $@
    exit $ret
}
die_in_error() {
    ret=$?
    if [[ $ret != 0 ]];then
        die $ret $@
    fi
}
#
# check if salt got errors:
# - First, check for fatal errors (retcode not in [0, 2]
# - in case of executions:
# - We will check for fatal errors in logs
# - We will check for any false return in output state structure
#
SALT_OUTFILE=$ROOT/.boot_salt_out
SALT_LOGFILE=$ROOT/.boot_salt_log
salt_call_wrapper() {
    outf="$SALT_OUTFILE"
    logf="$SALT_LOGFILE"
    rm -rf "$outf" "$logf" 2> /dev/null
    salt-call --retcode-passthrough --out=yaml --out-file="$outf" --log-file="$logf" -lquiet $@
    ret=$?
    #echo "result: false">>$outf
    if [[ $ret != 0 ]] && [[ $ret != 2 ]];then
        echo " [bs] salt-call ERROR, check $logf and $outf for details" 1>&2;
        ret=100
    elif grep  -q "No matching sls found" "$logf";then
        echo " [bs] salt-call  ERROR DETECTED : No matching sls found" 1>&2;
        ret=101
        no_check_output=y
    elif egrep -q "\[salt.state       \]\[ERROR   \]" "$logf";then
        echo " [bs] salt-call  ERROR DETECTED, check $logf for details" 1>&2;
        egrep "\[salt.state       \]\[ERROR   \]" "$logf" 1>&2;
        ret=102
        no_check_output=y
    else
        if egrep -q "result: false" "$outf";then
            echo " [bs] salt-call  ERROR DETECTED"
            echo " [bs] partial content of $outf, check this file for full output" 1>&2;
            egrep -B4 "result: false" "$outf" 1>&2;
            ret=104
            echo
        else
            ret=0
        fi
    fi
    #rm -rf "$outf" "$logf" 2> /dev/null
    echo $ret
}

echo " [bs] Create base directories"
for i in "$PILLAR" "$ROOT";do
    if [[ ! -d $i ]];then
        mkdir -pv $i
    fi
done

echo " [bs] Check package dependencies"
i_prereq || die_in_error " [bs] Failed install rerequisites"
if [[ ! -d "$MS/.git" ]];then
    git clone "$STATES_URL" "$MS" || die_in_error " [bs] Failed to download makina-states"
else
    cd $MS && git checkout master && git pull || die_in_error " [bs] Failed to update makina-states"
fi
# Script is now running in makina-states git location
cd $MS

# Check for virtualenv presence
if     [[ ! -e "$MS/bin/activate" ]] \
    || [[ ! -e "$MS/lib" ]] \
    || [[ ! -e "$MS/include" ]] \
    ;then
    echo " [bs] Creating virtualenv in $MS"
    virtualenv --no-site-packages --unzip-setuptools . &&\
    . bin/activate &&\
    easy_install -U setuptools &&\
    deactivate
fi

# virtualenv is present, activate it
if [[ -e bin/activate ]];then
    echo " [bs] Activating virtualenv in $MS"
    . bin/activate
fi

# Check for buildout things presence
if    [[ ! -e "$MS/bin/buildout" ]]\
   || [[ ! -e "$MS/parts" ]] \
   || [[ ! -e "$MS/develop-eggs" ]] \
    ;then
    echo " [bs] Launching buildout bootstrap for salt initialisation"
    python bootstrap.py
    ret=$?
    if [[ "$ret" != "0" ]];then
        rm -rf "$MS/parts" "$MS/develop-eggs"
        die $ret " [bs] Failed buildout bootstrap"
    fi
fi
# remove stale zmq egg (to relink on zmq3)
test="$(ldd $(find -L "$MS/eggs/pyzmq-"*egg -name *so)|grep zmq.so.1|wc -l)"
if [[ "$test" != "0" ]];then
    find -L "$MS/eggs/pyzmq-"*egg -maxdepth 0 -type d|xargs rm -rfv
fi
# detect incomplete buildout
# pyzmq check is for testing upgrade from libzmq to zmq3
if    [[ ! -e "$MS/bin/buildout" ]]\
    || [[ ! -e "$MS/bin/salt-ssh" ]]\
    || [[ ! -e "$MS/bin/salt" ]]\
    || [[ ! -e "$MS/bin/mypy" ]]\
    || [[ ! -e "$MS/.installed.cfg" ]]\
    || [[ $(find -L "$MS/eggs/pyzmq"* |wc -l) == "0" ]]\
    || [[ ! -e "$MS/src/salt/setup.py" ]]\
    || [[ ! -e "$MS/src/salt/setup.py" ]]\
    || [[ ! -e "$MS/src/docker/setup.py" ]]\
    || [[ ! -e "$MS/src/m2crypto/setup.py" ]]\
    || [[ ! -e "$MS/src/SaltTesting/setup.py" ]]\
    ;then
    echo " [bs] Launching buildout for salt initialisation"
    bin/buildout || die_in_error " [bs] Failed buildout"
    ret=$?
    if [[ "$ret" != "0" ]];then
        rm -rf "$MS/.installed.cfg"
        die $ret " [bs] Failed buildout"
    fi
fi

# Create a default top.sls in the pillar if not present
if [[ ! -f /srv/pillar/top.sls ]];then
    echo " [bs] creating default pillar's top.sls"
    cat > /srv/pillar/top.sls << EOF
#
# This is the top pillar configuration file, link here all your
# environment configurations files to their respective minions
#
base:
  '*':
EOF
fi
# Create a default setup in the tree if not present
if [[ ! -f /srv/salt/setup.sls ]];then
    echo " [bs] creating default salt's setup.sls"
    cat > /srv/salt/setup.sls << EOF
#
# Include here your various projet setup files
#
include:
  - makina-states.setup
EOF
fi
# Create a default top.sls in the tree if not present
if [[ ! -f /srv/salt/top.sls ]];then
    echo " [bs] creating default salt's top.sls"
    cat > /srv/salt/top.sls << EOF
#
# This is the salt states configuration file, link here all your
# environment states files to their respective minions
#
base:
  '*':
    - core
EOF
    if [[ ! -f /srv/salt/core.sls ]];then
        echo " [bs] creating default salt's core.sls"
            cat > /srv/salt/core.sls << EOF
#
# Dummy state file example
#
test:
  cmd.run:
    - name: salt '*' test.ping
EOF
    fi
fi

# TODO: comment
if [[ $(grep -- "- salt" /srv/pillar/top.sls|wc -l) == "0" ]];then
    sed -re "/('|\")\*('|\"):/ {
a\     - salt
}" -i /srv/pillar/top.sls
fi

# Create a default salt.sls in the pillar if not present
if [[ ! -f /srv/pillar/salt.sls ]];then
    echo " [bs] creating default pillar's salt.sls"
    cat > /srv/pillar/salt.sls << EOF
salt:
  minion:
    master: 127.0.0.1
    interface: 127.0.0.1
  master:
    interface: 127.0.0.1
EOF
fi

# --------- MASTERSALT
#TODO: comment
if [[ $SALT_BOOT == "mastersalt" ]] && [[ ! -f /srv/pillar/mastersalt.sls ]];then
    if [[ $(grep -- "- mastersalt" /srv/pillar/top.sls|wc -l) == "0" ]];then
        sed -re "/('|\")\*('|\"):/ {
a\     - mastersalt
}" -i /srv/pillar/top.sls
    fi
    if [[ ! -f /srv/pillar/mastersalt.sls ]];then
    cat > /srv/pillar/mastersalt.sls << EOF
mastersalt-minion:
  master: ${MASTERSALT}
  master_port: ${MASTERSALT_PORT}
EOF
    fi
fi

# --------- SALT install
if     [[ ! -e "/etc/salt" ]]\
    || [[ ! -e "/etc/salt/master" ]]\
    || [[ ! -e "/etc/salt/pki/minion/minion.pem" ]]\
    || [[ ! -e "/etc/salt/pki/master/master.pem" ]]\
    || [[ $(find /etc/salt/pki/master/minions -type f|wc -l) == "0" ]]\
    || [[ $(ps aux|grep salt-master|grep -v grep|wc -l) == "0" ]]\
    || [[ $(ps aux|grep salt-minion|grep -v grep|wc -l) == "0" ]]\
    ;then
    ds=y
    cd $MS
    echo " [bs] Upgrading salt base code source"
    bin/develop up -fv

    # kill salt running daemons if any
    ps aux|egrep "salt-(master|minion|syndic)" |awk '{print $2}'|xargs kill -9 &> /dev/null

    echo " [bs] Boostrapping salt"

    # create etc directory
    if [[ ! -e /etc/salt ]];then
        mkdir /etc/salt
    fi

     # capture output of a call of bootstrap states
     # by default makina-states.services.bootstrap but could be suffixed
    echo " [bs] Running salt states $bootstrap"
    ret=$(salt_call_wrapper --local state.sls $bootstrap)
    if [[ $ret != 0 ]];then
        echo " [bs] Failed bootstrap: $bootstrap !"
        exit $ret
    fi
    echo " [bs] Waiting for salt minion key to be accepted"
    sleep 10
    ps aux|grep salt-minion|awk '{print $2}'|xargs kill -9 &> /dev/null
    service salt-minion restart
    salt-key -A -y
    ret=$?
    cat $SALT_OUTFILE
    if [[ $ret != 0 ]];then
        echo " [bs] Failed accepting keys"
        exit $ret
    fi
    echo "changed=yes comment='salt installed'"
    touch /root/salt_bootstrap_done
fi

# --------- MASTERSALT
# in case of redoing a bootstrap for wiring on mastersalt
# after having already bootstrapped using a regular salt
# installation,
# we will run the specific mastersalt parts to wire
# on the global mastersalt
if [[ "$bootstrap" == "mastersalt" ]];then
    if     [[ ! -e "/etc/mastersalt" ]]\
        || [[ ! -e "/etc/mastersalt/master" ]]\
        || [[ ! -e "/etc/mastersalt/pki/minion/minion.pem" ]]\
        || [[ ! -e "/etc/mastersalt/pki/master/master.pem" ]]\
        || [[ $(find /etc/salt/pki/master/minions -type f|wc -l) == "0" ]]\
        || [[ $(ps aux|grep salt-master|grep mastersalt|grep -v grep|wc -l) == "0" ]]\
        || [[ $(ps aux|grep salt-minion|grep mastersalt|grep -v grep|wc -l) == "0" ]]\
        ;then
        ds=y
        cd $MS
        echo " [bs] Upgrading salt base code source"
        bin/develop up -fv

        # create etc/mastersalt
        if [[ ! -e /etc/mastersalt ]];then
            mkdir /etc/mastersalt
        fi

        # kill salt running daemons if any
        ps aux|egrep "salt-(master|minion|syndic)"|grep mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
        echo "Boostrapping salt"
        ret=$(salt_call_wrapper --local state.sls $bootstrap)
        cat $SALT_OUTFILE
        if [[ $ret != 0 ]];then
            echo "Failed bootstrap: $bootstrap !"
            exit $ret
        fi
        ps aux|grep salt-minion|grep mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
        service mastersalt-minion restart
        echo "changed=yes comment='mastersalt installed'"
    fi
fi

# TODO: comment
if [[ -z $ds ]];then
    echo 'changed="false" comment="already bootstrapped"'
fi

# -------------- MAKINA PROJECTS
if [[ -n $PROJECT_URL ]];then
    echo " [bs] Projects managment"
    project_mark="${PROJECT_URL}_${PROJECT_BRANCH}_${PROJECT_TOPSTATE}"
    project_mark="${project_mark//\//_}"
    project_tmpdir="$ROOT/.tmp_${project_mark}"
    project_mark="$ROOT/.${project_mark}"
    if [[ -f "${project_mark}" ]];then
        echo "$PROJECT_URL / $PROJECT_BRANCH / $PROJECT_TOPSTATE already done"
        echo "changed=\"false\" comment=\"$PROJECT_URL / $PROJECT_BRANCH / $PROJECT_TOPSTATE already done\""
    else
        BR=""
        if [[ -n $PROJECT_BRANCH ]];then
            BR="-b $PROJECT_BRANCH"
        fi
        if [[ -e "${project_tmpdir}" ]];then
            rm -rf "${project_tmpdir}"
        fi
        echo " [bs] Cloning  $PROJECT_URL / $PROJECT_BRANCH"
        git clone $BR "$PROJECT_URL" "${project_tmpdir}"
        ret=$?
        if [[ $ret != 0 ]];then
            echo " [bs] Failed to download project from $PROJECT_URL, or maybe the saltstack branch $PROJECT_BRANCH does not exist"
            exit -1
        fi
        rsync -az "${project_tmpdir}/" "$ROOT/"
        cd $ROOT
        if [[ -f setup.sls  ]] && [[ -z ${PROJECT_SETUPSTATE} ]];then
            PROJECT_SETUPSTATE=setup
        fi
        if [[ -n $PROJECT_SETUPSTATE ]];then
            echo " [bs] Launching saltstack setup ($PROJECT_SETUPSTATE) for $PROJECT_URL"
            ret=$(salt_call_wrapper --local state.sls $PROJECT_SETUPSTATE)
            cat $SALT_OUTFILE
            if [[ $ret != 0 ]];then
                echo " [bs] Failed to run setup.sls"
                exit -1
            fi
        fi
        echo " [bs] Launching saltstack top state ($PROJECT_TOPSTATE) for $PROJECT_URL"
        ret=$(salt_call_wrapper --local $PROJECT_TOPSTATE)
        if [[ $ret == 0 ]];then
            cat $SALT_OUTFILE
            echo  "changed=\"yes\" comment=\"$PROJECT_URL // $PROJECT_BRANCH // $PROJECT_TOPSTATE Installed\""
            touch "$project_mark"
        fi
    fi
fi
# vim:set et sts=5 ts=4 tw=0:

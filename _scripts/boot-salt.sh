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

RED="\\033[31m"
CYAN="\\033[36m"
NORMAL="\\033[0m"
DEBUG=${BOOT_SALT_DEBUG:-}

bs_log(){ echo -e "${RED}[bs] ${@}${NORMAL}"; }
warn_log() {
    bs_log "logs for salt executions availables in $SALT_OUTFILE / $SALT_LOGFILE"
}
die() {
    ret=$1
    shift
    warn_log
    echo -e "${CYAN}${@}${NORMAL}"
    exit -1
}
die_in_error() {
    ret=$?
    if [[ "$ret" != "0" ]];then
        die $ret $@
    fi
}

if [[ -f /etc/lsb-release ]];then
    . /etc/lsb-release
fi
base_packages=""
base_packages="$base_packages build-essential m4 libtool pkg-config autoconf gettext bzip2"
base_packages="$base_packages groff man-db automake libsigc++-2.0-dev tcl8.5 python-dev"
base_packages="$base_packages swig libssl-dev libyaml-dev debconf-utils python-virtualenv libzmq3-dev"
base_packages="$base_packages vim git"
UBUNTU_NEXT_RELEASE="saucy"
PILLAR=${PILLAR:-/srv/pillar}
ROOT=${ROOT:-/srv/salt}
MS=$ROOT/makina-states
VENV_PATH="/salt-venv"
CHRONO="$(date "+%F_%H-%M-%S")"
HOSTNAME="$(hostname)"

export PATH=$MS/bin:$PATH

# base sls file to run on a mastersalt master
MASTERSALT_MASTER_ST="makina-states.services.bootstrap_mastersalt_master"

# boot mode for mastersalt
# if mastersalt is set, automatic switch on mastersalt mode
if [[ -n $MASTERSALT ]];then
    bs_log " MasterSalt mode switch"
    SALT_BOOT="server"
    MASTERSALT_BOOT="mastersalt"
fi

# the current mastersalt.makinacorpus.net hostname
MASTERSALT_MAKINA_DNS="mastersalt.makina-corpus.net"
MASTERSALT_MAKINA_HOST="cloud-admin"

# host running the mastersalt salt-master
# - if we have not defined a mastersalt host,
#    default to localhost
#    if we are not on makinacorpus mastersalt
MASTERSALT_DEFAULT=""
if [[ $SALT_BOOT == "mastersalt" ]];then
    MASTERSALT_DEFAULT="localhost"
fi
if [[ "$HOSTNAME" == "$MASTERSALT_MAKINA_HOSTNAME" ]];then
    MASTERSALT="$MASTERSALT_MAKINA_DNS"
fi
MASTERSALT="${MASTERSALT:-$MASTERSALT_DEFAULT}"

# mark host as a salt-master if mastersalt.makina-corpus.net or localhost
if [[ -z "$MASTERSALT_MASTER" ]];then
    if [[ "$MASTERSALT" == "localhost" ]] \
        || [[ "$HOSTNAME" == "$MASTERSALT_MAKINA_HOSTNAME" ]];then
        MASTERSALT_MASTER="y"
    fi

fi
if [[ -n "$MASTERSALT_MASTER" ]];then
    MASTERSALT_BOOT="mastersalt_master"
fi

# set appropriate ports for mastersalt depening on the host and user input
MASTERSALT_DEFAULT_PORT="4606"
if [[ "$MASTERSALT" == "$MASTERSALT_MAKINA_DNS" ]];then
    MASTERSALT_DEFAULT_PORT="4506"
fi
MASTERSALT_PORT="${MASTERSALT_PORT:-$MASTERSALT_DEFAULT_PORT}"


STATES_URL="https://github.com/makinacorpus/makina-states.git"
PROJECT_URL="${PROJECT_URL:-}"
PROJECT_BRANCH="${PROJECT_BRANCH:-salt}"
PROJECT_TOPSTATE="${PROJECT_TOPSTATE:-state.highstate}"
PROJECT_SETUPSTATE="${PROJECT_SETUPSTATE}"
if [[ -z $SALT_BOOT ]];then
    SALT_BOOT="$1"
fi

# base sls bootstrap
bootstrap="makina-states.services.bootstrap"
mastersalt_bootstrap="$bootstrap"

if [[ -n "$SALT_BOOT" ]];then
    bootstrap="${bootstrap}_${SALT_BOOT}"
fi

if [[ -n "$MASTERSALT_BOOT" ]];then
    mastersalt_bootstrap="${bootstrap}_${MASTERSALT_BOOT}"
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
        bs_log "Installing ZeroMQ3"
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
    if [[ -n "$to_install" ]];then
        bs_log "Installing pre requisites: $to_install"
        echo 'changed="yes" comment="prerequisites installed"'
        apt-get update && apt-get install -y --force-yes $to_install
    fi
}

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
    if [[ "$ret" != "0" ]] && [[ "$ret" != "2" ]];then
        bs_log "salt-call ERROR, check $logf and $outf for details" 1>&2
        ret=100
    elif grep  -q "No matching sls found" "$logf";then
        bs_log "salt-call  ERROR DETECTED : No matching sls found" 1>&2
        ret=101
        no_check_output=y
    elif egrep -q "\[salt.state       \]\[ERROR   \]" "$logf";then
        bs_log "salt-call  ERROR DETECTED, check $logf for details" 1>&2
        egrep "\[salt.state       \]\[ERROR   \]" "$logf" 1>&2;
        ret=102
        no_check_output=y
    else
        if egrep -q "result: false" "$outf";then
            bs_log "salt-call  ERROR DETECTED"
            bs_log "partial content of $outf, check this file for full output" 1>&2
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
mastersalt_call_wrapper() {
    salt_call_wrapper -c /etc/mastersalt $@
}

bs_log "Create base directories"
for i in "$PILLAR" "$ROOT";do
    if [[ ! -d "$i" ]];then
        mkdir -pv $i
    fi
done

bs_log "Check package dependencies"
i_prereq || die_in_error " [bs] Failed install rerequisites"
if [[ ! -d "$MS/.git" ]];then
    git clone "$STATES_URL" "$MS" || die_in_error " [bs] Failed to download makina-states"
else
    cd $MS && git checkout master && git pull || die_in_error " [bs] Failed to update makina-states"
fi
# Script is now running in makina-states git location
# Check for virtualenv presence
REBOOTSTRAP="${SALT_REBOOTSTRAP}"
VENV_CONTENT="
bin/activate
bin/activate.csh
bin/activate.fish
bin/activate_this.py
bin/python
bin/python2*
bin/python3*
include/python*
lib/python*
local/bin/activate
local/bin/activate.csh
local/bin/activate.fish
local/bin/activate_this.py
local/bin/python
local/bin/python2*
local/bin/python3*
local/include/python*
local/lib/python*
"
cleanup_previous_venv() {
    if [[ -e "$1" ]];then
        old_d=$PWD
        cd $1
        CWD=$PWD
        for i in / /usr /usr/local;do
            if [[ "$CWD" == "$i" ]];then
                die 1 "[bs] wrong dir for venv: '$i'"
            fi
        done
        for item in $VENV_CONTENT;do
            for i in $(find $item -maxdepth 0 2>/dev/null);do
                bs_log "Cleaning $i"
                rm -rfv "$i"
                REBOOTSTRAP=y
            done
        done
        cd $old_d
    fi
}
cleanup_previous_venv $MS
cleanup_previous_venv /srv/salt-venv
cd $MS
if     [[ ! -e "$VENV_PATH/bin/activate" ]] \
    || [[ ! -e "$VENV_PATH/lib" ]] \
    || [[ ! -e "$VENV_PATH/include" ]] \
    ;then
    bs_log "Creating virtualenv in $VENV_PATH"
    virtualenv --no-site-packages --unzip-setuptools $VENV_PATH &&\
    . $VENV_PATH/bin/activate &&\
    easy_install -U setuptools &&\
    deactivate
    REBOOTSTRAP=y
fi

# virtualenv is present, activate it
if [[ -e "$VENV_PATH/bin/activate" ]];then
    bs_log "Activating virtualenv in $VENV_PATH"
    . $VENV_PATH/bin/activate
fi

# Check for buildout things presence
if    [[ ! -e "$MS/bin/buildout" ]]\
   || [[ ! -e "$MS/parts" ]] \
   || [[ -n "$REBOOTSTRAP" ]] \
   || [[ ! -e "$MS/develop-eggs" ]] \
    ;then
    bs_log "Launching buildout bootstrap for salt initialisation"
    python bootstrap.py
    ret=$?
    if [[ "$ret" != "0" ]];then
        rm -rf "$MS/parts" "$MS/develop-eggs"
        die $ret " [bs] Failed buildout bootstrap"
    fi
fi
# remove stale zmq egg (to relink on zmq3)
test="$(ldd $(find -L "$MS/eggs/pyzmq-"*egg -name *so 2>/dev/null) 2>/dev/null|grep zmq.so.1|wc -l)"
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
    || [[ -n "$REBOOTSTRAP" ]]\
    ;then
    bs_log "Launching buildout for salt initialisation"
    bin/buildout || die_in_error " [bs] Failed buildout"
    ret=$?
    if [[ "$ret" != "0" ]];then
        rm -rf "$MS/.installed.cfg"
        die $ret " [bs] Failed buildout"
    fi
fi

# Create a default top.sls in the pillar if not present
if [[ ! -f /srv/pillar/top.sls ]];then
    bs_log "creating default pillar's top.sls"
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
    bs_log "creating default salt's setup.sls"
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
    bs_log "creating default salt's top.sls"
    cat > /srv/salt/top.sls << EOF
#
# This is the salt states configuration file, link here all your
# environment states files to their respective minions
#
base:
  '*':
EOF
fi

# add core if not present
if [[ $(egrep -- "- core\s*$" /srv/salt/top.sls|wc -l) == "0" ]];then
    bs_log "Adding core to top file"
    sed -re "/('|\")\*('|\"):/ {
a\    - core
}" -i /srv/salt/top.sls
fi
if [[ ! -f /srv/salt/core.sls ]];then
    bs_log "creating default salt's core.sls"
    cat > /srv/salt/core.sls << EOF
#
# Dummy state file example
#
test:
  cmd.run:
    - name: salt '*' test.ping

EOF
fi

# add makina-salt.dev if not present
if [[ $(egrep -- "- makina-states\.dev\s*$" /srv/salt/top.sls|wc -l) == "0" ]];then
    bs_log "Adding makina-states.dev to top file"
    sed -re "/('|\")\*('|\"):/ {
a\    - makina-states.dev
}" -i /srv/salt/top.sls
fi

# TODO: comment
if [[ $(grep -- "- salt" /srv/pillar/top.sls|wc -l) == "0" ]];then
    sed -re "/('|\")\*('|\"):/ {
a\    - salt
}" -i /srv/pillar/top.sls
fi

# Create a default salt.sls in the pillar if not present
if [[ ! -f /srv/pillar/salt.sls ]];then
    bs_log "creating default pillar's salt.sls"
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
# Set default mastersalt  pillar
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

# global installation marker
NOW_INSTALLED=""

# --------- check if we need to run salt setup's
warn_log
RUN_SALT_SETUP=""
master_processes="$(ps aux|grep salt-master|grep -v mastersalt|grep -v grep|wc -l)"
minion_processes="$(ps aux|grep salt-minion|grep -v mastersalt|grep -v grep|wc -l)"
minion_keys="$(find /etc/salt/pki/master/minions -type f 2>/dev/null|wc -l)"
if     [[ ! -e "/etc/salt" ]]\
    || [[ ! -e "/etc/salt/master" ]]\
    || [[ ! -e "/etc/salt/pki/minion/minion.pem" ]]\
    || [[ ! -e "/etc/salt/pki/master/master.pem" ]]\
    || [[ "$minion_keys" == "0" ]]\
    || [[ "$master_processes" == "0" ]]\
    || [[ "$minion_processes" == "0" ]];then RUN_SALT_SETUP="1";fi

# --------- check if we need to run mastersalt setup's
RUN_MASTERSALT_SETUP=""
if [[ -n "$MASTERSALT" ]];then
    mminion_processes="$(ps aux|grep salt-minion|grep mastersalt|grep -v grep|wc -l)"
    mminion_keys="$(find /etc/mastersalt/pki/master/minions -type f 2>/dev/null|wc -l)"
    mmaster_processes="$(ps aux|grep salt-master|grep mastersalt|grep -v grep|wc -l)"
    if     [[ ! -e "/etc/mastersalt" ]]\
        || [[ ! -e "/etc/mastersalt/pki/minion/minion.pem" ]]\
        || [[ "$mminion_processes"  == "0" ]]\
        ;then RUN_MASTERSALT_SETUP="1";fi
    if [[ -n "$MASTERSALT_MASTER" ]];then
        if  [[ ! -e "/etc/mastersalt/pki/master/master.pem" ]]\
            || [[ "$mminion_keys" == "0" ]]\
            || [[ "$mmaster_processes" == "0" ]];then RUN_MASTERSALT_SETUP="1";fi
    fi
fi

# --------- Sources updates
if [[ -n "$RUN_SALT_SETUP" ]] || [[ -n "$RUN_MASTERSALT_SETUP" ]];then
    cd $MS
    bs_log "Upgrading salt base code source"
    bin/develop up -fv
fi

# --------- SALT install
if [[ -n "$RUN_SALT_SETUP" ]];then
    ds=y
    cd $MS

    # kill salt running daemons if any
    ps aux|egrep "salt-(master|minion|syndic)"|grep -v mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null

    bs_log "Boostrapping salt"
    # create etc directory
    if [[ ! -e /etc/salt ]];then mkdir /etc/salt;fi

    # capture output of a call of bootstrap states
    # by default makina-states.services.bootstrap but could be suffixed
    bs_log "Running salt states $bootstrap"
    ret=$(salt_call_wrapper --local state.sls $bootstrap)
    if [[ "$ret" != "0" ]];then
        bs_log "Failed bootstrap: $bootstrap !"
        exit -1
    fi
    if [[ -n "$DEBUG" ]];then cat $SALT_OUTFILE;fi
    # restart salt daemons
    bs_log "Forcing salt master restart"
    ps aux|grep salt-master|grep -v mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
    service salt-master restart
    sleep 10
    bs_log "Forcing salt minion restart"
    ps aux|grep salt-minion|grep -v mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
    service salt-minion restart
    # only accept key on fresh install (no keys stored)
    if [[ "$(ls -1 /etc/salt/pki/master/minions 2>/dev/null|wc -l)" == "0" ]];then
        bs_log "Waiting for salt minion key hand-shake"
        sleep 5
        salt-key -A -y
        ret=$?
        if [[ "$ret" != "0" ]];then
            bs_log "Failed accepting keys"
            exit -1
        fi
    else
        bs_log "Key already accepted, skipping key handshake"
    fi
    NOW_INSTALLED="y"
else
    bs_log "Skip salt installation, already done"
fi

# --------- MASTERSALT
# in case of redoing a bootstrap for wiring on mastersalt
# after having already bootstrapped using a regular salt
# installation,
# we will run the specific mastersalt parts to wire
# on the global mastersalt
if [[ -n "$RUN_MASTERSALT_SETUP" ]];then
    ds=y
    cd $MS

    # create etc/mastersalt
    if [[ ! -e /etc/mastersalt ]];then mkdir /etc/mastersalt;fi

    # kill salt running daemons if any
    ps aux|egrep "salt-(master|minion|syndic)"|grep mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null

    # if we are a mastersalt salt-master
    if [[ -n "$MASTERSALT_MASTER" ]];then
        # run mastersalt master+minion setup
        bs_log "Running mastersalt-master/minion setup ($MASTERSALT_MASTER_ST)"
        ret="$(mastersalt_call_wrapper --local state.sls $MASTERSALT_MASTER_ST)"
        if [[ -n "$DEBUG" ]];then cat $SALT_OUTFILE;fi
        if [[ "$ret" != "0" ]];then
            echo "Mastersalt: Failed bootstrap of mastersalt master"
            exit -1
        fi
    else
        # run mastersalt minion setup
        bs_log "Running mastersalt minion states $mastersalt_bootstrap"
        ret=$(mastersalt_call_wrapper --local state.sls $mastersalt_bootstrap)
        if [[ -n "$DEBUG" ]];then cat $SALT_OUTFILE;fi
        if [[ "$ret" != "0" ]];then
            echo "Mastersalt: Failed bootstrap: $mastersalt_bootstrap !"
            exit -1
        fi
    fi
    if [[ -n "$DEBUG" ]];then cat $SALT_OUTFILE;fi

    # kill mastersalt running daemons if any
    ps aux|egrep "salt-(master|minion|syndic)"|grep mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null

    # restart mastersalt salt-master after setup
    if [[ -n "$MASTERSALT_MASTER" ]];then
        bs_log "Forcing mastersalt master restart"
        ps aux|grep salt-master|grep mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
        service mastersalt-master restart
        sleep 10
    fi

    # restart mastersalt minion
    bs_log "Forcing mastersalt minion restart"
    ps aux|grep salt-minion|grep mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
    service mastersalt-minion restart

    # in case of a local mastersalt, auto accept the minion key
    if [[ "$MASTERSALT" == "localhost" ]];then
        # only accept key on fresh install (no keys stored)
        if [[ "$(ls -1 /etc/mastersalt/pki/master/minions 2>/dev/null|wc -l)" == "0" ]];then
            bs_log "Waiting for mastersalt minion key hand-shake"
            sleep 5
            mastersalt-key -A -y
            ret=$?
            if [[ "$ret" != "0" ]];then
                bs_log "Failed accepting mastersalt keys"
                exit -1
            fi
        else
            bs_log "Key already accepted, skipping mastersalt key handshake"
        fi
    else
        bs_log "*****************************************"
        bs_log "  [*] GO ACCEPT THE KEY ON MASTERSALT !!!"
        bs_log "*****************************************"
    fi
    NOW_INSTALLED="y"
else
    if [[ -n "$MASTERSALT" ]];then bs_log "Skip MasterSalt installation, already done";fi
fi

# --------- POST-SETUP
bs_log "Running salt states setup"
ret="$(salt_call_wrapper --local state.sls makina-states.setup)"
if [[ "$ret" != "0" ]];then
    bs_log "Failed post-setup"
    exit -1
fi
if [[ -n "$DEBUG" ]];then cat $SALT_OUTFILE;fi
warn_log
echo "changed=yes comment='salt post-setup run'"

if [[ -n "$MASTERSALT" ]];then
    bs_log "Running salt states setup for mastersalt"
    ret="$(mastersalt_call_wrapper --local state.sls makina-states.setup)"
    if [[ "$ret" != "0" ]];then
        bs_log "Failed post-setup for mastersalt"
        exit -1
    fi
    if [[ -n "$DEBUG" ]];then cat $SALT_OUTFILE;fi
    warn_log
    echo "changed=yes comment='mastersalt post-setup run'"
fi

# --------- stateful state return: mark as freshly installed
if [[ -n "$NOW_INSTALLED" ]];then
    warn_log
    echo "changed=yes comment='salt installed'"
fi

# --------- stateful state return: mark as already installed
if [[ -z "$ds" ]];then
    echo 'changed="false" comment="already bootstrapped"'
fi

# -------------- MAKINA PROJECTS
if [[ -n "$PROJECT_URL" ]];then
    bs_log "Projects managment"
    project_mark="${PROJECT_URL}_${PROJECT_BRANCH}_${PROJECT_TOPSTATE}"
    project_mark="${project_mark//\//_}"
    project_tmpdir="$ROOT/.tmp_${project_mark}"
    project_mark="$ROOT/.${project_mark}"
    if [[ -f "${project_mark}" ]];then
        echo "$PROJECT_URL / $PROJECT_BRANCH / $PROJECT_TOPSTATE already done"
        echo "changed=\"false\" comment=\"$PROJECT_URL / $PROJECT_BRANCH / $PROJECT_TOPSTATE already done\""
    else
        BR=""
    echo "changed=yes comment='salt installed'"
        if [[ -n $PROJECT_BRANCH ]];then
            BR="-b $PROJECT_BRANCH"
        fi
        if [[ -e "${project_tmpdir}" ]];then
            rm -rf "${project_tmpdir}"
        fi
        bs_log "Cloning  $PROJECT_URL / $PROJECT_BRANCH"
        git clone $BR "$PROJECT_URL" "${project_tmpdir}"
        ret=$?
        if [[ "$ret" != "0" ]];then
            bs_log "Failed to download project from $PROJECT_URL, or maybe the saltstack branch $PROJECT_BRANCH does not exist"
            exit -1
        fi
        rsync -az "${project_tmpdir}/" "$ROOT/"
        cd $ROOT
        if [[ -f setup.sls  ]] && [[ -z ${PROJECT_SETUPSTATE} ]];then
            PROJECT_SETUPSTATE=setup
        fi
        if [[ -n $PROJECT_SETUPSTATE ]];then
            bs_log "Launching saltstack setup ($PROJECT_SETUPSTATE) for $PROJECT_URL"
            ret=$(salt_call_wrapper --local state.sls $PROJECT_SETUPSTATE)
            if [[ -n "$DEBUG" ]];then cat $SALT_OUTFILE;fi
            if [[ "$ret" != "0" ]];then
                bs_log "Failed to run setup.sls"
                exit -1
            fi
        fi
        bs_log "Launching saltstack top state ($PROJECT_TOPSTATE) for $PROJECT_URL"
        ret=$(salt_call_wrapper --local $PROJECT_TOPSTATE)
        if [[ "$ret" == "0" ]];then
            if [[ -n "$DEBUG" ]];then cat $SALT_OUTFILE;fi
            echo  "changed=\"yes\" comment=\"$PROJECT_URL // $PROJECT_BRANCH // $PROJECT_TOPSTATE Installed\""
            touch "$project_mark"
        fi
    fi
fi
## vim:set et sts=5 ts=4 tw=0:

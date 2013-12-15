#!/usr/bin/env bash
#
# SEE MAKINA-STATES DOCS FOR FURTHER INSTRUCTIONS (or ../README.rst):
#
#    - https://github.com/makinacorpus/makina-states
#
# BOOTSTRAP MAKINA-STATES & SALT ON A DEBIAN / UBUNTU MACHINE FOR
# - install prerequisites
# - maybe configure pillar & states tree for master salt in /srv/mastersalt (default)
# - configure pillar & states tree for master salt in /srv/salt (default)
# - maybe bootstrap a makina-states based project
#
# Toubleshooting:
# - If the script fails, just relaunch it and it will continue where it was
# - You can safely relaunch it but be ware that it kills the salt daemons upon configure & setup
#   and consequently not safe for putting directly in salt states (with a cmd.run).
#

RED="\\033[31m"
CYAN="\\033[36m"
YELLOW="\\033[33m"
NORMAL="\\033[0m"
SALT_BOOT_DEBUG="${BOOT_SALT_DEBUG:-}"

bs_log(){
    echo -e "${RED}[bs] ${@}${NORMAL}";
}

bs_yellow_log(){
    echo -e "${YELLOW}[bs] ${@}${NORMAL}";
}

warn_log() {
    if [[ -e "$SALT_BOOT_OUTFILE" ]] || [[ -e "$SALT_BOOT_LOGFILE" ]];then
        bs_log "logs for salt executions availables in:"
        if [[ -e "$SALT_BOOT_OUTFILE" ]];then
            bs_log "    - $SALT_BOOT_OUTFILE"
        fi
        if [[ -e "$SALT_BOOT_LOGFILE" ]];then
            bs_log "    - $SALT_BOOT_LOGFILE"
        fi
        if [[ -e "$SALT_BOOT_CMDFILE" ]];then
            bs_log "    - $SALT_BOOT_CMDFILE"
        fi 
    fi
}

die() {
    warn_log
    echo -e "${CYAN}${@}${NORMAL}"
    exit -1
}

die_in_error() {
    ret="$?"
    if [[ "$ret" != "0" ]];then
        echo -e "${CYAN}${@}${NORMAL}"
        exit $ret
    fi
}

test_online() {
    ping -W 10 -c 1 8.8.8.8 &> /dev/null
    echo $?
}

detect_os() {
    # make as a function to be copy/pasted as-is in multiple scripts
    IS_UBUNTU=""
    IS_DEBIAN=""
    if [[ -e $CONF_ROOT/lsb-release ]];then
        . $CONF_ROOT/lsb-release
        if [[ "$DISTRIB_CODENAME" == "lucid" ]]\
            || [[ "$DISTRIB_CODENAME" == "maverick" ]]\
            || [[ "$DISTRIB_CODENAME" == "natty" ]]\
            || [[ "$DISTRIB_CODENAME" == "oneiric" ]]\
            || [[ "$DISTRIB_CODENAME" == "precise" ]]\
            || [[ "$DISTRIB_CODENAME" == "quantal" ]]\
            ;then
            EARLY_UBUNTU=y
            BEFORE_RARING=y
        fi
        if [[ "$DISTRIB_CODENAME" == "raring" ]] || [[ -n "$EARLY_UBUNTU" ]];then
            BEFORE_SAUCY=y
        fi
    fi
    if [[ -e $CONF_ROOT/os-release ]];then
        . $CONF_ROOT/os-release
        OS_RELEASE_ID=$(egrep ^ID= $CONF_ROOT/os-release|sed -re "s/ID=//g")
        OS_RELEASE_NAME=$(egrep ^NAME= $CONF_ROOT/os-release|sed -re "s/NAME=//g")
        OS_RELEASE_VERSION=$(egrep ^VERSION= $CONF_ROOT/os-release|sed -re "s/VERSION=//g")
        OS_RELEASE_PRETTY_NAME=$(egrep ^VERSION= $CONF_ROOT/os-release|sed -re "s/VERSION=//g")
    fi
    if [[ -e $CONF_ROOT/debian_version ]] && [[ "$OS_RELEASE_ID" == "debian" ]] && [[ "$DISTRIB_ID" != "Ubuntu" ]];then
        IS_DEBIAN="y"
        DISTRIB_CODENAME="$(echo $OS_RELEASE_PRETTY_NAME |sed -re "s/.*\((.*)\).*/\1/g")"
    fi
    if [[ $IS_UBUNTU ]];then
        DISTRIB_NEXT_RELEASE="saucy"
        DISTRIB_BACKPORT="$DISTRIB_NEXT_RELEASE"
    elif [[ $IS_DEBIAN ]];then
        if [[ "$DISTRIB_CODENAME"  == "wheezy" ]];then
            DISTRIB_NEXT_RELEASE="jessie"
        elif [[ "$DISTRIB_CODENAME"  == "squeeze" ]];then
            DISTRIB_NEXT_RELEASE="wheezy"
        fi
        DISTRIB_BACKPORT="wheezy-backports"
    fi
}

set_vars() {
    detect_os
    HOSTNAME="$(hostname)"
    CHRONO="$(date "+%F_%H-%M-%S")"
    lxc_ps=$(which lxc-ps &> /dev/null)
    if [[ "$(egrep "^container=" /proc/1/environ|wc -l)" == "0" ]];then
        # we are in a container !
        lxc_ps=""
    fi
    if [[ -n $lxc_ps ]];then
        PS="$lxc_ps --host --"
    else
        PS="$(which ps)"
    fi
    BASE_PACKAGES=""
    BASE_PACKAGES="$BASE_PACKAGES build-essential m4 libtool pkg-config autoconf gettext bzip2"
    BASE_PACKAGES="$BASE_PACKAGES groff man-db automake libsigc++-2.0-dev tcl8.5 python-dev"
    BASE_PACKAGES="$BASE_PACKAGES swig libssl-dev libyaml-dev debconf-utils python-virtualenv"
    BASE_PACKAGES="$BASE_PACKAGES vim git rsync"
    BASE_PACKAGES="$BASE_PACKAGES libzmq3-dev"
    STATES_URL="https://github.com/makinacorpus/makina-states.git"
    PREFIX="${PREFIX:-/srv}"
    PILLAR="${PILLAR:-$PREFIX/pillar}"
    SALT_BOOT_NOCONFIRM="${SALT_BOOT_NOCONFIRM:-}"
    ROOT="${ROOT:-$PREFIX/salt}"
    SALT_BOOT_OUTFILE="$MS/.boot_salt_out"
    SALT_BOOT_LOGFILE="$MS/.boot_salt_log"
    MS="$ROOT/makina-states"
    MASTERSALT_PILLAR="${MASTERSALT_PILLAR:-$PREFIX/mastersalt-pillar}"
    MASTERSALT_ROOT="${MASTERSALT_ROOT:-$PREFIX/mastersalt}"
    MASTERSALT_MS="$MASTERSALT_ROOT/makina-states"
    TMPDIR="${TMPDIR:-"/tmp"}"
    VENV_PATH="${VENV_PATH:-"/salt-venv"}"
    CONF_ROOT="${CONF_ROOT:-"/etc"}"
    CONF_PREFIX="${CONF_PREFIX:-"$CONF_ROOT/salt"}"
    MCONF_PREFIX="${MCONF_PREFIX:-"$CONF_ROOT/mastersalt"}"
    ETC_INIT="${ETC_INIT:-"$CONF_ROOT/init"}"
    # global installation marker
    SALT_BOOT_NOW_INSTALLED=""
    # the current mastersalt.makinacorpus.net hostname
    MASTERSALT_MAKINA_DNS="mastersalt.makina-corpus.net"
    MASTERSALT_MAKINA_HOST="cloud-admin"
    # base sls bootstrap
    bootstrap_pref="makina-states.bootstrap"
    mastersalt_bootstrap_pref="${bootstrap_pref}.mastersalt"
    SALT_PRESENT=""
    if [[ -e ${ETC_INIT}/ersalt-master.conf ]] || [[ -e ${ETC_INIT}.d/salt-master ]];then
        SALT_PRESENT="y"
        SALT_BOOT_DEFAULT="server"
    elif [[ -e ${ETC_INIT}/salt-minion.conf ]] || [[ -e ${ETC_INIT}.d/salt-minion ]];then
        SALT_PRESENT="y"
        SALT_BOOT_DEFAULT="server"
    fi
    SALT_BOOT_DEFAULT="server"
    SALT_BOOT_INPUTED="${SALT_BOOT}"
    SALT_BOOT="${SALT_BOOT:-$SALT_BOOT_DEFAULT}"
    # boot mode for mastersalt
    MASTERSALT_BOOT_DEFAULT="minion"
    # if mastersalt is set, automatic switch on mastersalt mode
    if [[ -n $MASTERSALT_MASTER ]];then
        MASTERSALT_BOOT_DEFAULT="master"
    fi
    if [[ -e ${ETC_INIT}/mastersalt-master.conf ]] || [[ -e ${ETC_INIT}.d/mastersalt-master ]];then
        MASTERSALT_PRESENT="y"
        MASTERSALT_BOOT_DEFAULT=master
    elif [[ -e ${ETC_INIT}/mastersalt-minion.conf ]] || [[ -e ${ETC_INIT}.d/mastersalt-minion ]];then
        MASTERSALT_PRESENT="y"
        MASTERSALT_BOOT_DEFAULT=minion
    fi
    MASTERSALT_BOOT_INPUTED="${MASTERSALT_BOOT}"
    MASTERSALT_BOOT="${MASTERSALT_BOOT:-$MASTERSALT_BOOT_DEFAULT}"
    if [[ "$MASTERSALT_BOOT" == "master"  ]];then
        MASTERSALT_MASTER="y"
    fi
    MASTERSALT_INPUTED="${MASTERSALT}"
    # host running the mastersalt salt-master
    # - if we have not defined a mastersalt host,
    #    default to localhost
    #    if we are not on makinacorpus mastersalt
    MASTERSALT_DEFAULT=""
    if [[ -z "$MASTERSALT" ]];then
        if [[ "$HOSTNAME" == "$MASTERSALT_MAKINA_HOSTNAME" ]];then
            MASTERSALT="$MASTERSALT_MAKINA_DNS"
        fi
        # mark host as a salt-master if mastersalt.makina-corpus.net or localhost
        if [[ -n "$MASTERSALT_MASTER" ]];then
            MASTERSALT="localhost"
        fi
    fi
    MASTERSALT="${MASTERSALT:-$MASTERSALT_DEFAULT}"
    # set appropriate ports for mastersalt depening on the host and user input
    MASTERSALT_DEFAULT_PORT="4606"
    if [[ "$MASTERSALT" == "$MASTERSALT_MAKINA_DNS" ]];then
        MASTERSALT_DEFAULT_PORT="4606"
    fi
    MASTERSALT_PORT="${MASTERSALT_PORT:-$MASTERSALT_DEFAULT_PORT}"
    if [[ -n "$SALT_BOOT" ]];then
        bootstrap="${bootstrap_pref}.${SALT_BOOT}"
    fi
    if [[ -n "$MASTERSALT_BOOT" ]];then
        mastersalt_bootstrap="${mastersalt_bootstrap_pref}_${MASTERSALT_BOOT}"
    fi
    USE_MASTERSALT=""
    if [[ -n "$MASTERSALT" ]] || [[ -n $MASTERSALT_PRESENT ]];then
        USE_MASTERSALT="y"
    fi

    # --------- PROJECT VARS
    MAKINA_PROJECTS="makina-projects"
    PROJECTS_PATH="/srv/projects"
    PROJECT_URL="${PROJECT_URL:-}"
    PROJECT_BRANCH="${PROJECT_BRANCH:-salt}"
    PROJECT_NAME="${PROJECT_NAME:-}"
    PROJECT_TOPSLS="${PROJECT_TOPSLS:-}"
    PROJECT_SETUPSTATE="${PROJECT_SETUPSTATE:-}"
    PROJECT_PATH="$PROJECTS_PATH/$PROJECT_NAME"
    PROJECTS_SALT_PATH="$ROOT/$MAKINA_PROJECTS"
    PROJECTS_PILLAR_PATH="$PILLAR/$MAKINA_PROJECTS"
    PROJECT_PILLAR_LINK="$PROJECTS_PILLAR_PATH/$PROJECT_NAME"
    PROJECT_PILLAR_PATH="$PROJECTS_PATH/$PROJECT_NAME/pillar"
    PROJECT_PILLAR_FILE="$PROJECT_PILLAR_PATH/init.sls"
    PROJECT_SALT_LINK="$ROOT/$MAKINA_PROJECTS/$PROJECT_NAME"
    PROJECT_SALT_PATH="$PROJECT_PATH/salt"
    PROJECT_TOPSLS_DEFAULT="$MAKINA_PROJECTS/$PROJECT_NAME/top.sls"
    PROJECT_TOPSTATE_DEFAULT="${MAKINA_PROJECTS}.${PROJECT_NAME}.top"
    PROJECT_SETUPSTATE_DEFAULT="${MAKINA_PROJECTS}.${PROJECT_NAME}.setup"
    PROJECT_PILLAR_STATE="${MAKINA_PROJECTS}.${PROJECT_NAME}"
    export BASE_PACKAGES STATES_URL PREFIX PILLAR SALT_BOOT_NOCONFIRM MASTERSALT_PILLAR
    export MASTERSALT_ROOT ROOT MASTERSALT_MS MS ETC_INIT MASTERSALT_MAKINA_DNS MASTERSALT_MAKINA_HOST
    export VENV_PATH CONF_ROOT CONF_PREFIX MASTERSALT_BOOT SALT_BOOT
    export MAKINA_PROJECTS PROJECTS_PATH PROJECT_URL PROJECT_BRANCH PROJECT_NAME PROJECT_TOPSLS
    export PROJECT_SETUPSTATE PROJECT_PATH PROJECTS_SALT_PATH PROJECTS_PILLAR_PATH PROJECT_PILLAR_LINK
    export PROJECT_PILLAR_PATH PROJECT_PILLAR_FILE PROJECT_SALT_LINK PROJECT_SALT_PATH PROJECT_TOPSLS_DEFAULT
    export PROJECT_TOPSTATE_DEFAULT PROJECT_SETUPSTATE_DEFAULT PROJECT_PILLAR_STATE
    if [[ -n "$PROJECT_URL" ]];then
        if [[ -z "$PROJECT_NAME" ]];then
            die "Please provide a \$PROJECT_NAME"
        fi
    fi
}

# --------- PROGRAM START

recap_(){
    bs_yellow_log "--------------------------------------------------"
    bs_yellow_log " MAKINA-STATES BOOTSTRAPPER"
    bs_yellow_log "   - $0"
    bs_yellow_log " Those informations have been written to:"
    bs_yellow_log "   - $TMPDIR/boot_salt_top"
    bs_yellow_log "--------------------------------------------------"
    bs_yellow_log "HOST variables:"
    bs_yellow_log "---------------"
    bs_log "HOSTNAME: $HOSTNAME"
    bs_log "DATE: $CHRONO"
    bs_yellow_log "---------------"
    bs_yellow_log "SALT variables:"
    bs_yellow_log "---------------"
    bs_log "SALT_BOOT_INPUTED: $SALT_BOOT_INPUTED"
    bs_log "SALT_BOOT: $SALT_BOOT"
    bs_log "SALT_PILLAR: $PILLAR"
    bs_log "SALT_ROOT: $ROOT"
    bs_log "bootstrap: $bootstrap"
    if [[ -n $SALT_BOOT_SKIP_SETUP ]];then
        bs_log "SALT_BOOT_SKIP_SETUP: $SALT_BOOT_SKIP_SETUP"
    fi
    if [[  -n "$USE_MASTERSALT" ]];then
        bs_yellow_log "---------------------"
        bs_yellow_log "MASTERSALT variables:"
        bs_yellow_log "---------------------"
        if [[ -n $MASTERSALT_MASTER ]];then
            bs_log "MASTERSALT_MASTER: $MASTERSALT_MASTER"
        fi
        bs_log "MASTERSALT_INPUTED: $MASTERSALT_INPUTED"
        bs_log "MASTERSALT: $MASTERSALT"
        bs_log "MASTERSALT_PRESENT: $MASTERSALT_PRESENT"
        bs_log "MASTERSALT_PORT: $MASTERSALT_PORT"
        bs_log "MASTERSALT_ROOT: $MASTERSALT_ROOT"
        bs_log "MASTERSALT_PILLAR: $MASTERSALT_PILLAR"
        bs_log "MASTERSALT_BOOT: $MASTERSALT_BOOT"
        bs_log "mastersalt_bootstrap: $mastersalt_bootstrap"
    fi
    if [[ -n $PROJECT_URL ]];then
        bs_yellow_log "-----"
        bs_yellow_log "PROJECT variables:"
        bs_yellow_log "-----"
        bs_log "PROJECT_URL:  ${PROJECT_UR}"
        bs_log "PROJECT_BRANCH: ${PROJECT_BRANCH}"
        bs_log "PROJECT_NAME: ${PROJECT_NAME}"
    fi
    bs_yellow_log "---------------------------------------------------"
    if [[ -z $SALT_BOOT_NOCONFIRM ]];then
        bs_yellow_log "The installation will continue in 60 secondes"
        bs_yellow_log "unless you press enter to continue or C-c to abort"
        bs_yellow_log "To not have this confirmation message, do:"
        bs_yellow_log "    export SALT_BOOT_NOCONFIRM='1'"
        bs_yellow_log "---------------------------------------------------"
        read -t 60
    fi
    # export variables to support a restart
    export SALT_BOOT_INPUTED="$SALT_BOOT_INPUTED"
    export SALT_BOOT="$SALT_BOOT"
    export SALT_PILLAR="$PILLAR"
    export SALT_ROOT="$ROOT"
    if [[ -n $SALT_BOOT_SKIP_SETUP ]];then
        export SALT_BOOT_SKIP_SETUP="$SALT_BOOT_SKIP_SETUP"
    fi
    if [[  -n "$USE_MASTERSALT" ]];then
        if [[ -n $MASTERSALT_MASTER ]];then
            export MASTERSALT_MASTER="$MASTERSALT_MASTER"
        fi
        export MASTERSALT="$MASTERSALT"
        export MASTERSALT_PRESENT="$MASTERSALT_PRESENT"
        export MASTERSALT_PORT="$MASTERSALT_PORT"
        export MASTERSALT_ROOT="$MASTERSALT_ROOT"
        export MASTERSALT_PILLAR="$MASTERSALT_PILLAR"
        export MASTERSALT_BOOT="$MASTERSALT_BOOT"
    fi
    if [[ -n $PROJECT_URL ]];then
        export PROJECT_URL="${PROJECT_UR}"
        export PROJECT_BRANCH="${PROJECT_BRANCH}"
        export PROJECT_NAME="${PROJECT_NAME}"
    fi
}

recap() {
    recap_
    recap_ > "$TMPDIR/boot_salt_top"
}

is_apt_installed() {
    if [[ "$(dpkg-query -s $@ 2>/dev/null|egrep "^Status:"|grep installed|wc -l)"  == "0" ]];then
        echo "no"
    else
        echo "yes"
    fi
}

lazy_apt_get_install() {
    to_install=""
    for i in $@;do
         if [[ "$(is_apt_installed $i)"  != "yes" ]];then
             to_install="$to_install $i"
         fi
    done
    if [[ -n "$to_install" ]];then
        bs_log " [bs] Installing $to_install"
        apt-get install -y --force-yes $to_install
    fi
}

setup_backports() {
    # on ubuntu enable backports release repos, & on debian just backport
    if [[ -n "$BEFORE_SAUCY" ]] && [[ -n "$IS_UBUNTU" ]];then
        bs_log "Activating backport from $DISTRIB_BACKPORT to $DISTRIB_CODENAME"
        cp  $CONF_ROOT/apt/sources.list "$CONF_ROOT/apt/sources.list.$CHRONO.sav"
        sed -re "s/${DISTRIB_CODENAME}/${DISTRIB_BACKPORT}/g" -i $CONF_ROOT/apt/sources.list
    fi
    if [[ -n "$IS_DEBIAN" ]];then
        bs_log "Activating backport from $DISTRIB_BACKPORT to $DISTRIB_CODENAME"
        cp  $CONF_ROOT/apt/sources.list "$CONF_ROOT/apt/sources.list.$CHRONO.sav"
        sed "/^deb.*$DISTRIB_BACKPORT/d" -i $CONF_ROOT/apt/sources.list
        echo "#backport added by boot-salt">/tmp/aptsrc
        egrep "^deb.* $DISTRIB_CODENAME " $CONF_ROOT/apt/sources.list|sed -re "s/$DISTRIB_CODENAME/$DISTRIB_BACKPORT/g" > /tmp/aptsrc
        cat /tmp/aptsrc >> $CONF_ROOT/apt/sources.list
        rm -f /tmp/aptsrc
    fi

}

teardown_backports() {
    # on ubuntu disable backports release repos, & on debian just backport
    if [[ -n "$BEFORE_SAUCY" ]] && [[ -n "$IS_UBUNTU" ]];then
        bs_log "Removing backport from $DISTRIB_BACKPORT to $DISTRIB_CODENAME"
        sed -re "s/${DISTRIB_BACKPORT}/${DISTRIB_CODENAME}/g" -i $CONF_ROOT/apt/sources.list
    fi
    # leave the backport in placs on debian
    #if [[ -n $IS_DEBIAN ]];then
    #    bs_log "Removing backport from $DISTRIB_BACKPORT to $DISTRIB_CODENAME"
    #    sed "/^#.*added.*boot-sa/d" -i $CONF_ROOT/apt/sources.list
    #    sed "/^deb.*$DISTRIB_BACKPORT/d" -i $CONF_ROOT/apt/sources.list
    #fi
}

i_prereq() {
    to_install=""
    bs_log "Check package dependencies"
    lazy_apt_get_install python-software-properties
    # XXX: only lts package in this ppa
    if     [[ "$(is_apt_installed libzmq3    )"  == "no" ]] \
        || [[ "$(is_apt_installed libzmq3-dev)"  == "no" ]];\
        then
        bs_log "Installing ZeroMQ3"
        setup_backports
        apt-get remove -y --force-yes libzmq libzmq1 libzmq-dev &> /dev/null
        apt-get update -qq && lazy_apt_get_install libzmq3-dev
        ret="$?"
        teardown_backports && apt-get update
        if [[ $ret != "0" ]];then
            die $ret "Install of zmq3 failed"
        fi
    fi
    for i in $BASE_PACKAGES;do
        if [[ $(dpkg-query -s $i 2>/dev/null|egrep "^Status:"|grep installed|wc -l)  == "0" ]];then
            to_install="$to_install $i"
        fi
    done
    if [[ -n "$to_install" ]];then
        bs_log "Installing pre requisites: $to_install"
        echo 'changed="yes" comment="prerequisites installed"'
        apt-get update && lazy_apt_get_install $to_install
    fi
}

# check if salt got errors:
# - First, check for fatal errors (retcode not in [0, 2]
# - in case of executions:
# - We will check for fatal errors in logs
# - We will check for any false return in output state structure
salt_call_wrapper_() {
    salt_call_prefix=$1;shift
    outf="$SALT_BOOT_OUTFILE"
    logf="$SALT_BOOT_LOGFILE"
    cmdf="$SALT_BOOT_CMDFILE"
    rm -rf "$outf" "$logf" 2> /dev/null
    saltargs=" --retcode-passthrough --out=yaml --out-file="$outf" --log-file="$logf""
    if [[ -n $SALT_BOOT_DEBUG ]];then
        saltargs="$saltargs -lall"
    else
        saltargs="$saltargs -lquiet"
    fi
    $salt_call_prefix/bin/salt-call $saltargs $@
    echo "$(date): $salt_call_prefix/bin/salt-call $saltargs $@" >> "$cmdf"
    ret=$?
    #echo "result: false">>$outf
    if [[ "$ret" != "0" ]] && [[ "$ret" != "2" ]];then
        bs_log "salt-call ERROR, check $logf and $outf for details" 1>&2
        ret=100
    elif [[ -e "logf" ]];then
        if grep  -q "No matching sls found" "$logf";then
            bs_log "salt-call  ERROR DETECTED : No matching sls found" 1>&2
            ret=101
            no_check_output=y
        elif egrep -q "\[salt.state       \]\[ERROR   \]" "$logf";then
            bs_log "salt-call  ERROR DETECTED, check $logf for details" 1>&2
            egrep "\[salt.state       \]\[ERROR   \]" "$logf" 1>&2;
            ret=102
            no_check_output=y
        fi
    elif [[ -e "outf" ]];then
        if egrep -q "result: false" "$outf";then
            bs_log "salt-call  ERROR DETECTED"
            bs_log "partial content of $outf, check this file for full output" 1>&2
            egrep -B4 "result: false" "$outf" 1>&2;
            ret=104
            echo
        else
            ret=0
        fi
    else
        ret=0
    fi
    #rm -rf "$outf" "$logf" 2> /dev/null
    echo $ret
}

salt_call_wrapper() {
    SALT_BOOT_OUTFILE="$MS/.boot_salt_out"
    SALT_BOOT_LOGFILE="$MS/.boot_salt_log"
    SALT_BOOT_CMDFILE="$MS/.boot_salt_cmd"
    salt_call_wrapper_ $MS $@
}

mastersalt_call_wrapper() {
    SALT_BOOT_OUTFILE="$MASTERSALT_MS/.boot_salt_out"
    SALT_BOOT_LOGFILE="$MASTERSALT_MS/.boot_salt_log"
    SALT_BOOT_CMDFILE="$MASTERSALT_MS/.boot_salt_cmd"
    salt_call_wrapper_ $MASTERSALT_MS -c $MCONF_PREFIX $@
}

get_grain() {
    salt-call --local grains.get $1 --out=raw 2>/dev/null
}

set_grain() {
    grain=$1
    bs_log " [bs] Testing salt grain '$grain'"
    if [[ "$(get_grain $grain)" != *"True"* ]];then
        bs_log " [bs] Setting salt grain: $grain=true "
        salt-call --local grains.setval $grain true
        # sync grains rigth now, do not wait for reboot
        die_in_error "setting $grain"
        salt-call --local saltutil.sync_grains &> /dev/null
    else
        bs_log " [bs] Grain '$grain' already set"
    fi
}

check_restartmarker_and_maybe_restart() {
    if [[ -z $SALT_BOOT_IN_RESTART ]];then
        if [[ -n "$SALT_BOOT_NEEDS_RESTART" ]];then
            touch "$MS/.bootsalt_need_restart"
        fi
        if [[ -e "$MS/.bootsalt_need_restart" ]] && [[ -z "$SALT_BOOT_NO_RESTART" ]];then
            chmod +x "$MS/_scripts/boot-salt.sh"
            export SALT_BOOT_NO_RESTART="1"
            export SALT_BOOT_IN_RESTART="1"
            bootsalt="$MS/_scripts/boot-salt.sh"
            bs_log "Restarting $bootsalt which needs to update itself"
            "$bootsalt" && rm -f "$MS/.bootsalt_need_restart"
            exit $?
        fi
    fi
}

setup_and_maybe_update_code() {
    bs_log "Create base directories"
    for i in "$PILLAR" "$ROOT";do
        if [[ ! -d "$i" ]];then
            mkdir -pv "$i"
        fi
    done
    if [[  -n "$USE_MASTERSALT" ]];then
        for i in "$MASTERSALT_PILLAR" "$MASTERSALT_ROOT";do
            if [[ ! -d "$i" ]];then
                mkdir -pv "$i"
            fi
        done
    fi
    MSS="$MS"
    if [[  -n "$USE_MASTERSALT" ]];then
        MSS="$MSS $MASTERSALT_MS"
    fi
    is_offline="$(test_online)"
    minion_keys="$(find $CONF_PREFIX/pki/master/minions -type f 2>/dev/null|wc -l)"
    if [[ "$is_offline" != "0" ]];then
        if [[ ! -e $CONF_PREFIX ]]\
            || [[ "$minion_keys" == "0" ]]\
            || [[ ! -e "$MS/src/salt" ]]\
            || [[ ! -e "$MS/bin/salt-call" ]]\
            || [[ ! -e "$MS/bin/salt" ]];then
            bs_log "Offline mode and installation not enougthly completed, bailing out"
            exit -1
        fi
    fi
    if [[ "$is_offline" == "0" ]]\
        && [[ -z "$SALT_BOOT_IN_RESTART" ]]\
        && [[ -z "$SALT_BOOT_SKIP_CHECKOUTS" ]];then
        i_prereq || die_in_error " [bs] Failed install rerequisites"
        for ms in $MSS;do
            if [[ ! -d "$ms/.git" ]];then
                git clone "$STATES_URL" "$ms"
                SALT_BOOT_NEEDS_RESTART="1"
                if [[ "$?" == "0" ]];then
                    die_in_error " [bs] Downloaded makina-states ($ms)"
                else
                    die_in_error " [bs] Failed to download makina-states ($ms)"
                fi
            fi
            #chmod +x $MS/_scripts/install_salt_modules.sh
            #"$MS/_scripts/install_salt_modules.sh" "$ROOT"
            cd "$ms"
            if [[ ! -d src ]];then
                mkdir src
            fi
            for i in "$ms" "$ms/src/"*;do
                if [[ -e "$i/.git" ]];then
                    sed -re "s/filemode =.*/filemode=false/g" -i $i/.git/config 2>/dev/null
                    branch="master"
                    if [[ "$i" == "$ms/src/salt" ]];then
                        branch="develop"
                    fi
                    bs_log "Upgrading $i"
                    cd $i
                    git fetch origin &&\
                        git diff origin/$branch --exit-code &> /dev/null
                    if [[ "$?" != "0" ]];then
                        SALT_BOOT_NEEDS_RESTART=1
                        bs_log "update is necessary"
                    fi && git merge --ff-only origin/$branch
                    if [[ "$?" == "0" ]];then
                        die_in_error " [bs] Downloaded/updateded $i"
                    else
                        die_in_error " [bs] Failed to download/update $i"
                    fi
                fi
            done
        done
    fi
    check_restartmarker_and_maybe_restart
}

cleanup_previous_venv() {
    if [[ -e "$1" ]];then
        old_d="$PWD"
        cd "$1"
        CWD="$PWD"
        for i in / /usr /usr/local;do
            if [[ "$CWD" == "$i" ]];then
                die 1 "[bs] wrong dir for venv: '$i'"
            fi
        done
        for item in $VENV_CONTENT;do
            for i in $(find $item -maxdepth 0 2>/dev/null);do
                bs_log "Cleaning $i"
                rm -rfv "$i"
                REBOOTSTRAP="y"
            done
        done
        cd "$old_d"
    fi
}
setup_virtualenv() {
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
}

run_ms_buildout() {
    ms=$1
    cd $ms
    # Check for buildout things presence
    if    [[ ! -e "$ms/bin/buildout" ]]\
       || [[ ! -e "$ms/parts" ]] \
       || [[ -n "$REBOOTSTRAP" ]] \
       || [[ ! -e "$ms/develop-eggs" ]] \
        ;then
        bs_log "Launching buildout bootstrap for salt initialisation ($ms)"
        python bootstrap.py
        ret=$?
        if [[ "$ret" != "0" ]];then
            rm -rf "$ms/parts" "$ms/develop-eggs"
            die $ret " [bs] Failed buildout bootstrap ($ms)"
        fi
    fi
    # remove stale zmq egg (to relink on zmq3)
    test="$(ldd $(find -L "$ms/eggs/pyzmq-"*egg -name *so 2>/dev/null) 2>/dev/null|grep zmq.so.1|wc -l)"
    if [[ "$test" != "0" ]];then
        find -L "$ms/eggs/pyzmq-"*egg -maxdepth 0 -type d|xargs rm -rfv
    fi
    # detect incomplete buildout
    # pyzmq check is for testing upgrade from libzmq to zmq3
    if    [[ ! -e "$ms/bin/buildout" ]]\
        || [[ ! -e "$ms/bin/salt-ssh" ]]\
        || [[ ! -e "$ms/bin/salt" ]]\
        || [[ ! -e "$ms/bin/salt-syndic" ]]\
        || [[ ! -e "$ms/bin/mypy" ]]\
        || [[ ! -e "$ms/.installed.cfg" ]]\
        || [[ $(find -L "$ms/eggs/pyzmq"* |wc -l) == "0" ]]\
        || [[ ! -e "$ms/src/salt/setup.py" ]]\
        || [[ ! -e "$ms/src/salt/setup.py" ]]\
        || [[ ! -e "$ms/src/docker/setup.py" ]]\
        || [[ ! -e "$ms/src/m2crypto/setup.py" ]]\
        || [[ ! -e "$ms/src/SaltTesting/setup.py" ]]\
        || [[ -n "$REBOOTSTRAP" ]]\
        ;then
        cd $ms
        bs_log "Launching buildout for salt initialisation ($ms)"
        bin/buildout || die_in_error " [bs] Failed buildout ($ms)"
        ret=$?
        if [[ "$ret" != "0" ]];then
            rm -rf "$ms/.installed.cfg"
            die $ret " [bs] Failed buildout in $ms"
        fi
    fi
}

install_buildouts() {
    run_ms_buildout $MS
    if [[  -n "$USE_MASTERSALT" ]];then
        if [[ ! -e $MASTERSALT_ROOT/makina-states/.installed.cfg ]];then
            rsync -a $MS/ $MASTERSALT_ROOT/makina-states/
            cd $MASTERSALT_ROOT/makina-states
            rm -rf .installed.cfg .mr.developer.cfg parts
        fi
        run_ms_buildout $MASTERSALT_ROOT/makina-states/
    fi
}

create_salt_skeleton(){
    PILLAR_ROOTS="$PILLAR"
    if [[  -n "$USE_MASTERSALT" ]];then
        PILLAR_ROOTS="$PILLAR_ROOTS $MASTERSALT_PILLAR"
    fi
    for pillar_root in $PILLAR_ROOTS;do
        # Create a default top.sls in the pillar if not present
        if [[ ! -f $pillar_root/top.sls ]];then
            bs_log "creating default $pillar_root/top.sls"
            cat > $pillar_root/top.sls << EOF
#
# This is the top pillar configuration file, link here all your
# environment configurations files to their respective minions
#
base:
  '*':
EOF
        fi
    done
    SETUPS_FILES="$ROOT/setup.sls"
    if [[  -n "$USE_MASTERSALT" ]];then
        SETUPS_FILES="$SETUPS_FILES $MASTERSALT_ROOT/setup.sls"
    fi
    for stp in $SETUPS_FILES;do
        # Create a default setup in the tree if not present
        if [[ ! -f $stp ]];then
            bs_log "creating default $stp"
            cat > $stp << EOF
#
# Include here your various projet setup files
#
base:
  '*':
    - makina-states.setup
EOF
        fi
        if [[ "$(egrep  "^(  '\*':)" $stp|wc -l)" == "0" ]];then
            bs_log "Old installation detected for $stp, trying to migrate it"
            cp $ROOT/setup.sls $stp.${CHRONO}.bak
            sed  "/include:/{
a base:
a \  '*':
}" -i $ROOT/setup.sls
            sed -re "s/^  -/    -/g"  -i $stp
            sed -re "/^include:/d"  -i $stp
        fi
    done

    # Create a default top.sls in the tree if not present
    TOPS_FILES="$ROOT/top.sls"
    if [[ -n "$MASTERSALT_MASTER" ]];then
        TOPS_FILES="$TOPS_FILES $MASTERSALT_ROOT/top.sls"
    fi
    for topf in $TOPS_FILES;do
        if [[ ! -f $topf ]];then
            bs_log "creating default salt's $topf"
            cat > "$topf" << EOF
#
# This is the salt states configuration file, link here all your
# environment states files to their respective minions
#
base:
  '*':
EOF
        fi
        # add makina-salt.dev if not present
        if [[ $(egrep -- "- makina-states\.dev\s*$" $topf|wc -l) == "0" ]];then
        bs_log "Adding makina-states.dev to $topf"
            sed -re "/('|\")\*('|\"):/ {
a\    {% if grains.get('makina.devhost', False) %}
a\    - makina-states.dev
a\    {% endif %}
}" -i $topf
        fi
    done
    for pillar_root in $PILLAR;do
        if [[ $(grep -- "- salt" $PILLAR/top.sls|wc -l) == "0" ]];then
            sed -re "/('|\")\*('|\"):/ {
a\    - salt
}" -i "$pillar_root/top.sls"
        fi
        # Create a default salt.sls in the pillar if not present
        if [[ ! -f "$pillar_root/salt.sls" ]];then
            bs_log "creating default pillar's salt.sls"
            cat > "$pillar_root/salt.sls" << EOF
salt:
  minion:
    master: 127.0.0.1
    interface: 127.0.0.1
  master:
    interface: 127.0.0.1
EOF
        fi
    done
    # --------- MASTERSALT
    # Set default mastersalt  pillar
    if [[ "$SALT_BOOT" == "mastersalt" ]] && [[ ! -f "$MASTERSALT_PILLAR/mastersalt.sls" ]];then
        if [[ $(grep -- "- mastersalt" "$MASTERSALT_PILLAR/top.sls"|wc -l) == "0" ]];then
            sed -re "/('|\")\*('|\"):/ {
a\    - mastersalt
}" -i "$MASTERSALT_PILLAR/top.sls"
        fi
        if [[ ! -f "$MASTERSALT_PILLAR/mastersalt.sls" ]];then
    cat > "$MASTERSALT_PILLAR/mastersalt.sls" << EOF
mastersalt:
  minion:
      master: ${MASTERSALT}
      master_port: ${MASTERSALT_PORT}
EOF
        fi
    fi
}

# ------------ SALT INSTALLATION PROCESS

get_minion_id() {
    cat $CONF_PREFIX/minion_id 2> /dev/null
}

install_salt_env() {
    # --------- check if we need to run salt setup's
    warn_log
    master_processes="$($PS aux|grep salt-master|grep -v mastersalt|grep -v grep|wc -l)"
    minion_processes="$($PS aux|grep salt-minion|grep -v mastersalt|grep -v grep|wc -l)"
    # in case of failed setup, do not do extra reinstall
    # in master/minion restart well
    if [[ "$master_processes" == "0" ]]\
        && [[ -e "$CONF_PREFIX/pki/minion/master.pem" ]];then
        service salt-master restart
        sleep 2
    fi
    if [[ "$minion_processes" == "0" ]]\
        && [[ -e "$CONF_PREFIX/pki/minion/minion.pem" ]];then
        service salt-minion restart
        sleep 2
    fi
    master_processes="$($PS aux|grep salt-master|grep -v mastersalt|grep -v grep|wc -l)"
    minion_processes="$($PS aux|grep salt-minion|grep -v mastersalt|grep -v grep|wc -l)"
    RUN_SALT_SETUP=""
    if     [[ ! -e "$CONF_PREFIX" ]]\
        || [[ ! -e "$CONF_PREFIX/master" ]]\
        || [[ -e "$MS/.reboostrap" ]]\
        || [[ ! -e "$CONF_PREFIX/pki/minion/minion.pem" ]]\
        || [[ ! -e "$CONF_PREFIX/pki/master/master.pem" ]]\
        || [[ "$master_processes" == "0" ]]\
        || [[ "$minion_processes" == "0" ]];then
        if [[ -e "$MS/.reboostrap" ]];then
            rm -f "$MS/.rebootstrap"
        fi
        RUN_SALT_SETUP="1"
    fi

    # --------- SALT install
    if [[ -n "$RUN_SALT_SETUP" ]];then
        ds=y
        # kill salt running daemons if any
        $PS aux|egrep "salt-(master|minion|syndic)"|grep -v mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null

        bs_log "Boostrapping salt"
        # create etc directory
        if [[ ! -e $CONF_PREFIX ]];then mkdir $CONF_PREFIX;fi
        if [[ ! -e $CONF_PREFIX/minion ]];then
            cat > $CONF_PREFIX/minion << EOF
file_roots: {"base":["$ROOT"]}
EOF
        fi
        # capture output of a call of bootstrap states
        # by default makina-states.services.bootstrap but could be suffixed
        bs_log "Running makina-states bootstrap: $bootstrap"
        ret="$(salt_call_wrapper --local $(get_saltcall_args) state.sls $bootstrap)"
        if [[ "$ret" != "0" ]];then
            bs_log "Failed bootstrap: $bootstrap !"
            exit -1
        fi
        if [[ -n "$SALT_BOOT_DEBUG" ]];then cat $SALT_BOOT_OUTFILE;fi
        # restart salt daemons
        SALT_BOOT_NOW_INSTALLED="y"
    else
        bs_log "Skip salt installation, already done"
    fi
}

make_association() {
    minion_keys="$(find $CONF_PREFIX/pki/master/minions -type f 2>/dev/null|wc -l)"
    minion_id="$(get_minion_id)"
    registered=""
    if [[ "$(salt_call_wrapper test.ping)" == "0" ]]\
        && [[ "$minion_keys" != "0" ]]\
        ;then
        bs_log "Salt minion \"$minion_id\" already registered on master"
        minion_id="$(get_minion_id)"
        registered="1"
    else
        bs_log "Forcing salt master restart"
        $PS aux|grep salt-master|grep -v mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
        service salt-master restart
        sleep 10
        bs_log "Forcing salt minion restart"
        $PS aux|grep salt-minion|grep -v mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
        service salt-minion restart
        bs_log "Waiting for salt minion key hand-shake"
        sleep 2
        minion_id="$(get_minion_id)"
    fi
    # only accept key on fresh install (no keys stored)
    if [[ -z "$registered" ]] &\
        [[ "$(ls -1 $CONF_PREFIX/pki/master/minions/$minion_id 2>/dev/null|wc -l)" == "0" ]];then
        minion_id="$(get_minion_id)"
        if [[ -z "$minion_id" ]];then
            die_in_error "Minion did not start correctly, the minion_id cache file is empty"
        fi
        minion_id="$(get_minion_id)"
        salt-key -y -a "$minion_id"
        ret="$?"
        if [[ "$ret" != "0" ]];then
            bs_log "Failed accepting keys"
            exit -1
        fi
        # restarting minion to handshake with its valid key and
        # let it be in a working state
        for i in `seq 60`;do
            $PS aux|grep salt-minion|grep -v mastersalt|awk '{print $3}'|xargs kill -9 &> /dev/null
            service salt-minion restart
            resultping="1"
            for j in `seq 10`;do
                resultping="$(salt_call_wrapper test.ping)"
                if [[ "$resultping" != "0" ]];then
                    bs_yellow_log " sub challenge try $j/$i"
                    sleep 1
                else
                    break
                fi
            done
            if [[ "$resultping" != "0" ]];then
                bs_log "Failed challenge salt keys on master, retry $i/60"
                challenged_ms=""
            else
                challenged_ms="y"
                bs_log "Successfull challenge salt keys on master"
                break
            fi
        done
        if [[ -z "$challenged_ms" ]];then
            bs_log "Failed accepting salt key on master for $minion_id"
            exit -1
        fi
    else
        if [[ -z $registered ]];then
            bs_log "Minion key absent, installation inconsistent,  bailing out"
            exit -1
        fi
    fi
}

maybe_install_mastersalt_env() {
    # --------- check if we need to run mastersalt setup's
    RUN_MASTERSALT_SETUP=""
    if [[ -n "$USE_MASTERSALT" ]];then
        mminion_processes="$($PS aux|grep salt-minion|grep mastersalt|grep -v grep|wc -l)"
        mminion_keys="$(find $MCONF_PREFIX/pki/master/minions -type f 2>/dev/null|wc -l)"
        mmaster_processes="$($PS aux|grep salt-master|grep mastersalt|grep -v grep|wc -l)"
        if     [[ ! -e "$MCONF_PREFIX" ]]\
            || [[ ! -e "$MCONF_PREFIX/pki/minion/minion.pem" ]]\
            || [[ ! -e "$MASTERSALT_MS/.reboostrap" ]]\
            || [[ "$mminion_processes"  == "0" ]]\
            ;then
            if [[ -e "$MASTERSALT_MS/.reboostrap" ]];then
                rm -f "$MASTERSALT_MS/.rebootstrap"
            fi
            RUN_MASTERSALT_SETUP="1"
        fi
        if [[ -n "$MASTERSALT_MASTER" ]];then
            if  [[ ! -e "$MCONF_PREFIX/pki/master/master.pem" ]]\
                || [[ "$mminion_keys" == "0" ]]\
                || [[ "$mmaster_processes" == "0" ]];then RUN_MASTERSALT_SETUP="1";fi
        fi
    fi

    # --------- MASTERSALT
    # in case of redoing a bootstrap for wiring on mastersalt
    # after having already bootstrapped using a regular salt
    # installation,
    # we will run the specific mastersalt parts to wire
    # on the global mastersalt
    if [[ -n "$RUN_MASTERSALT_SETUP" ]];then
        ds=y
        # create etc/mastersalt
        if [[ ! -e $MCONF_PREFIX ]];then mkdir $MCONF_PREFIX;fi
        if [[ ! -e $MCONF_PREFIX/minion ]];then
            cat > $CONF_PREFIX/minion << EOF
file_roots: {"base":["$MASTERSALT_ROOT"]}
EOF
        fi

        # kill salt running daemons if any
        $PS aux|egrep "salt-(master|minion|syndic)"|grep mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null

        # run mastersalt master+minion setup
        bs_log "Running mastersalt bootstrap: $mastersalt_bootstrap"
        run_state="mastersalt_call_wrapper --local $(get_mastersaltcall_args) state.sls"
        ret="$($run_state $mastersalt_bootstrap)"
        if [[ -n "$SALT_BOOT_DEBUG" ]];then cat $SALT_BOOT_OUTFILE;fi
        if [[ "$ret" != "0" ]];then
            echo "Mastersalt: Failed bootstrap: $mastersalt_bootstrap"
            exit -1
        fi
        if [[ -n "$SALT_BOOT_DEBUG" ]];then cat $SALT_BOOT_OUTFILE;fi

        # kill mastersalt running daemons if any
        $PS aux|egrep "salt-(master|minion|syndic)"|grep mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null

        # restart mastersalt salt-master after setup
        if [[ -n "$MASTERSALT_MASTER" ]];then
            bs_log "Forcing mastersalt master restart"
            $PS aux|grep salt-master|grep mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
            service mastersalt-master restart
            sleep 10
        fi

        # restart mastersalt minion
        bs_log "Forcing mastersalt minion restart"
        $PS aux|grep salt-minion|grep mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
        service mastersalt-minion restart
        # in case of a local mastersalt, auto accept the minion key
        sleep 5
        minion_id="$(cat $CONF_PREFIX/minion_id &> /dev/null)"
        if [[ -z "$minion_id" ]];then
            minion_id="<minionid>"
        fi
        if [[ "$(mastersalt_call_wrapper test.ping)" == "0" ]];then
            bs_log "Mastersalt minion \"$minion_id\" already registered on $MASTERSALT"
        else
            # disable the localhost trick to harmonize the challenge workflow
            #if [[ "$MASTERSALT" == "localhost" ]];then
            #    # only accept key on fresh install (no keys stored)
            #    if [[ "$(ls -1 $MCONF_PREFIX/pki/master/minions 2>/dev/null|wc -l)" == "0" ]];then
            #        bs_log "Waiting for mastersalt minion key hand-shake"
            #        sleep 5
            #        mastersalt-key -A -y
            #        ret=$?
            #        if [[ "$ret" != "0" ]];then
            #            bs_log "Failed accepting mastersalt keys"
            #            exit -1
            #        fi
            #    else
            #        if [[ "$(mastersalt_call_wrapper test.ping)" != "0" ]];then
            #            bs_log "MasterSalt minion already registered on $MASTERSALT"
            #        else
            #            bs_log "Failed accepting mastersalt keys"
            #            exit -1
            #        fi
            #    fi
            #else
            if [[ -z "$MASTERSALT_NO_CHALLENGE" ]];then
                bs_log "****************************************************************"
                bs_log "  [bs] GO ACCEPT THE KEY ON MASTERSALT ($MASTERSALT) !!! "
                bs_log "  [bs] You need on this box to run mastersalt-key -y -a $minion_id"
                bs_log "****************************************************************"
                bs_log " We are going to wait 10 minutes for you to setup the minion on mastersalt and"
                bs_log " setup an entry for this specific minion"
                bs_log " export MASTERSALT_NO_CHALLENGE=1 to remove the temposisation (enter to continue when done)"
                read -t "$((10*60))"
                # sleep 15 seconds giving time for the minion to wake up
            else
                bs_log "  [*} No temporisation for challenge, trying to spawn the minion"
            fi
            for i in `seq 60`;do
                $PS aux|grep salt-minion|grep mastersalt|awk '{print $3}'|xargs kill -9 &> /dev/null
                service mastersalt-minion restart
                resultping="1"
                for j in `seq 10`;do
                    resultping="$(mastersalt_call_wrapper test.ping)"
                    if [[ "$resultping" != "0" ]];then
                        bs_yellow_log " sub challenge try $j/$i"
                        sleep 1
                    else
                        break
                    fi
                done
                if [[ "$resultping" != "0" ]];then
                    bs_log "Failed challenge mastersalt keys on $MASTERSALT, retry $i/60"
                    challenged_ms=""
                else
                    challenged_ms="y"
                    bs_log "Successfull challenge mastersalt keys on $MASTERSALT"
                    break
                fi
            done
            if [[ -z "$challenged_ms" ]];then
                bs_log "Failed accepting mastersalt key on $MASTERSALT for $minion_çid"
                exit -1
            fi
            #fi
        fi
        SALT_BOOT_NOW_INSTALLED="y"
    else
        if [[ -n "$MASTERSALT" ]];then bs_log "Skip MasterSalt installation, already done";fi
    fi
}

get_module_args() {
    arg=""
    for i in $@;do
        arg="$arg -m \"$i/_modules\""
    done
    echo $arg
}

get_saltcall_args() {
    get_module_args "$ROOT" "$MS "
}
get_mastersaltcall_args() {
    get_module_args "$MASTERSALT_ROOT" "$MASTERSALT_MS"
}


# --------- POST-SETUP

maybe_setup_mastersalt_env() {
    # IMPORTANT: MASTERSALT BEFORE SALT !!!
    if [[ -z $SALT_BOOT_SKIP_SETUP ]] && [[ -n "$USE_MASTERSALT" ]];then
        bs_log "Running makina-states setup for mastersalt"
        LOCAL="$(get_mastersaltcall_args)"
        if [[ "$(mastersalt_call_wrapper test.ping)" != "0" ]];then
            LOCAL="--local $LOCAL"
            bs_yellow_log " [bs] mastersalt setup running offline !"
        fi
        ret="$(mastersalt_call_wrapper $LOCAL state.sls makina-states.setup)"
        if [[ "$ret" != "0" ]];then
            bs_log "Failed post-setup for mastersalt"
            exit -1
        fi
        if [[ -n "$SALT_BOOT_DEBUG" ]];then cat $SALT_BOOT_OUTFILE;fi
        warn_log
        echo "changed=yes comment='mastersalt post-setup run'"
    fi
}


setup_salt_env() {
    if [[ -z "$SALT_BOOT_SKIP_SETUP" ]];then
        bs_log "Running makina-states setup"
        LOCAL="$(get_saltcall_args)"
        if [[ "$(salt_call_wrapper test.ping)" != "0" ]];then
            bs_yellow_log " [bs] salt setup running offline !"
            LOCAL="--local $LOCAL"
        fi
        ret="$(salt_call_wrapper $LOCAL state.sls makina-states.setup)"
        if [[ "$ret" != "0" ]];then
            bs_log "Failed post-setup"
            exit -1
        fi
    fi
    if [[ -n "$SALT_BOOT_DEBUG" ]];then cat $SALT_BOOT_OUTFILE;fi
    warn_log
    echo "changed=yes comment='salt post-setup run'"

    # --------- stateful state return: mark as freshly installed
    if [[ -n "$SALT_BOOT_NOW_INSTALLED" ]];then
        warn_log
        echo "changed=yes comment='salt installed and configured'"
    fi

}

install_salt_envs() {
    # XXX: important mastersalt must be configured before salt
    # to override possible local settings.
    maybe_install_mastersalt_env
    maybe_setup_mastersalt_env
    install_salt_env
    make_association
    setup_salt_env
    # --------- stateful state return: mark as already installed
    if [[ -z "$ds" ]];then
        echo 'changed="false" comment="already bootstrapped"'
    fi
}

# -------------- MAKINA PROJECTS

maybe_install_projects() {
    if [[ -n "$PROJECT_URL" ]];then
        bs_log "Projects managment"
        setup_grain="makina.projects.${PROJECT_NAME}.boot.setup"
        project_grain="makina.projects.${PROJECT_NAME}.boot.top"
        BR=""
        if [[ -n "$PROJECT_BRANCH" ]];then
            BR="-b $PROJECT_BRANCH"
        fi
        FORCE_PROJECT_TOP="${FORCE_PROJECT_TOP:-}"
        FORCE_PROJECT_SETUP="${FORCE_PROJECT_SETUP:-}"
        # force state rerun if project is not there anymore
        if [[ ! -e "$PROJECT_PATH" ]];then
            mkdir -pv "$PROJECT_PATH"
        fi
        checkout=""
        if [[ ! -e "$PROJECT_SALT_PATH/.git/config" ]];then
            bs_log "Cloning  $PROJECT_URL@$PROJECT_BRANCH in $PROJECT_SALT_PATH"
            git clone $BR "$PROJECT_URL" "$PROJECT_SALT_PATH"
            ret="$?"
            if [[ "$ret" != "0" ]];then
                bs_log "Failed to download project from $PROJECT_URL, or maybe the saltstack branch $PROJECT_BRANCH does not exist"
                exit -1
            fi
            if [[ ! -e "$PROJECT_SALT_PATH/.git/config" ]];then
                bs_log "Incomplete download project from $PROJECT_URL, see $PROJECT_SALT_PATH"
                exit -1
            fi
            if [[ -e  "$PROJECT_SALT_LINK" ]];then
                rm -f "$PROJECT_SALT_LINK"
            fi
            ln -sf "$PROJECT_SALT_PATH" "$PROJECT_SALT_LINK"
            checkout="y"
            FORCE_PROJECT_SETUP="y"
            FORCE_PROJECT_TOP="y"
        fi
        #if [[ -z $checkout ]];then
        #    bs_log "Update code from branch: $PROJECT_BRANCH"
        #    cd $PROJECT_SALT_PATH
        #    git fetch origin
        #    git reset --hard "origin/$PROJECT_BRANCH"
        #fi
        changed="false"
        O_SALT_BOOT_LOGFILE="$SALT_BOOT_LOGFILE"
        O_SALT_BOOT_OUTFILE="$SALT_BOOT_OUTFILE"
        if [[ -f "$PROJECT_SALT_PATH/setup.sls"  ]] && [[ -z ${PROJECT_SETUPSTATE} ]];then
            PROJECT_SETUPSTATE="$PROJECT_SETUPSTATE_DEFAULT"
        fi
        if [[ -f "$ROOT/${PROJECT_TOPSLS_DEFAULT}"  ]] && [[ -z ${PROJECT_TOPSLS} ]];then
            PROJECT_TOPSLS="$PROJECT_TOPSLS_DEFAULT"
        fi
        PROJECT_TOPSTATE="$(echo ${PROJECT_TOPSLS}|sed -re 's/\//./g' -e 's/\.sls//g')"
        if [[ ! -d "$PROJECT_PILLAR_PATH" ]];then
            mkdir -p "$PROJECT_PILLAR_PATH"
            bs_log "Creating pillar container in $PROJECT_PILLAR_PATH"
        fi
        if [[ ! -d "$PROJECTS_PILLAR_PATH" ]];then
            mkdir -p "$PROJECTS_PILLAR_PATH"
            bs_log "Creating $MAKINA_PROJECTS pillar container in $PILLAR"
        fi
        if [[ ! -e "$PROJECT_PILLAR_LINK" ]];then
            bs_log "Linking project $PROJECT_NAME pillar in $PILLAR"
            echo ln -sf "$PROJECT_PILLAR_PATH" "$PROJECT_PILLAR_LINK"
            ln -sf "$PROJECT_PILLAR_PATH" "$PROJECT_PILLAR_LINK"
        fi
        if [[ ! -e "$PROJECT_PILLAR_FILE" ]];then
            if [[ ! -e "$PROJECT_SALT_PATH/PILLAR.sample.sls" ]];then
                bs_log "Creating empty project $PROJECT_NAME pillar in $PROJECT_PILLAR_FILE"
                touch "$PROJECT_SALT_PATH/PILLAR.sample.sls"
            fi
            bs_log "Linking project $PROJECT_NAME pillar in $PROJECT_PILLAR_FILE"
            ln -sf "$PROJECT_SALT_PATH/PILLAR.sample.sls" "$PROJECT_PILLAR_FILE"
        fi
        if [[ $(grep -- "- $PROJECT_PILLAR_STATE" $PILLAR/top.sls|wc -l) == "0" ]];then
            bs_log "including $PROJECT_NAME pillar in $PILLAR/top.sls"
            sed -re "/('|\")\*('|\"):/ {
a\    - $PROJECT_PILLAR_STATE
}" -i $PILLAR/top.sls
        fi
        if [[ "$(get_grain $setup_grain)" != *"True"* ]] || [[ -n $FORCE_PROJECT_SETUP ]];then
            if [[ -n $PROJECT_SETUPSTATE ]];then
                SALT_BOOT_LOGFILE="$PROJECT_SALT_PATH/.salt_setup_log.log"
                SALT_BOOT_OUTFILE="$PROJECT_SALT_PATH/.salt_setup_out.log"
                bs_log "Running salt Setup: $PROJECT_URL@$PROJECT_BRANCH[$PROJECT_SETUPSTATE]"
                ret=$(salt_call_wrapper state.sls $PROJECT_SETUPSTATE)
                if [[ -n "$SALT_BOOT_DEBUG" ]];then cat $SALT_BOOT_OUTFILE;fi
                if [[ "$ret" != "0" ]];then
                    bs_log "Failed to run $PROJECT_SETUPSTATE"
                    exit -1
                else
                    warn_log
                    set_grain "$setup_grain"
                fi
                changed="true"
            fi
        else
            bs_log "Setup: $PROJECT_URL@$PROJECT_BRANCH[$PROJECT_SETUPSTATE] already done (remove grain: $setup_grain to redo)"
            echo "changed=\"false\" comment=\"$PROJECT_URL@$PROJECT_BRANCH[$PROJECT_SETUPSTATE] already done\""
        fi
        if [[ "$(get_grain $project_grain)" != *"True"* ]] || [[ -n $FORCE_PROJECT_TOP ]];then
            if [[ -n $PROJECT_TOPSLS ]];then
                SALT_BOOT_LOGFILE="$PROJECT_SALT_PATH/.salt_top_log.log"
                SALT_BOOT_OUTFILE="$PROJECT_SALT_PATH/.salt_top_out.log"
                bs_log "Running salt Top state: $PROJECT_URL@$PROJECT_BRANCH[$PROJECT_TOPSLS]"
                ret=$(salt_call_wrapper state.top "$PROJECT_TOPSLS")
                if [[ -n "$SALT_BOOT_DEBUG" ]];then cat $SALT_BOOT_OUTFILE;fi
                if [[ "$ret" != "0" ]];then
                    bs_log "Failed to run $PROJECT_TOPSLS"
                    exit -1
                else
                    warn_log
                    set_grain "$project_grain"
                fi
                changed="true"
            fi
        else
            bs_log "Top state: $PROJECT_URL@$PROJECT_BRANCH[$PROJECT_TOPSLS] already done (remove grain: $project_grain to redo)"
            echo "changed=\"false\" comment=\"$PROJECT_URL@$PROJECT_BRANCH[$PROJECT_TOPSLS] already done\""
        fi
        if [[ $(grep -- "- $PROJECT_TOPSTATE" "$ROOT/top.sls"|wc -l) == "0" ]];then
            sed -re "/('|\")\*('|\"):/ {
a\    - $PROJECT_TOPSTATE
}" -i "$ROOT/top.sls"
        fi
        if [[ $(grep -- "- $PROJECT_SETUPSTATE" "$ROOT/setup.sls"|wc -l) == "0" ]];then
            sed -re "/('|\")\*('|\"):/ {
a\    - $PROJECT_SETUPSTATE
}" -i "$ROOT/setup.sls"
        fi
        bs_log "Installation finished, dont forget to install/verify:"
        bs_log "    - $PROJECT_SETUPSTATE in $ROOT/setup.sls"
        bs_log "    - $PROJECT_TOPSLS in $ROOT/top.sls"
        bs_log "    - in $PROJECT_PILLAR_FILE"
        if [[ "$changed" == "false" ]];then
            echo "changed=\"$changed\" comment=\"already installed\""
        else
            echo "changed=\"$changed\" comment=\"installed\""
        fi
        SALT_BOOT_LOGFILE="$O_SALT_BOOT_LOGFILE"
        SALT_BOOT_OUTFILE="$O_SALT_BOOT_OUTFILE"
    fi
}

cleanup_old_installs() {
    for i in "$MS" "$MASTERSALT_MS";do
        if [[ -e "$i" ]];then
            for j in "$i/bin/"mastersalt*;do
                bs_log "Cleanup $j"
                if [[ -e "$j" ]];then
                    rm -rvf "$j"
                fi
            done
        fi
    done
    if [[ ! -d "$MASTERSALT_PILLAR" ]] \
        && [[ -e "$PILLAR/mastersalt.sls" ]] \
        && [[ -e /usr/bin/mastersalt ]];then
        bs_log "copy old pillar to new $MASTERSALT_PILLAR"
        cp -rf "$PILLAR" "$MASTERSALT_PILLAR"
        rm -vf "$PILLAR/mastersalt.sls"
        if [[ -e "$MASTERSALT_PILLAR/salt.sls" ]];then
            rm -vf "$MASTERSALT_PILLAR/salt.sls"
        fi
        sed -re "/^\s*- salt$/d" -i "$MASTERSALT_PILLAR/top.sls"
        sed -re "/^\s*- mastersalt$/d" -i "$PILLAR/top.sls"

    fi
    if [[ "$(egrep "bootstrapped\.salt" $MCONF_PREFIX/grains &>/dev/null |wc -l)" != "0" ]];then
        bs_log "Cleanup old mastersalt grains"
        sed -re "/bootstrap\.salt/d" -i $MCONF_PREFIX/grains
        mastersalt_call_wrapper --local saltutil.sync_grains
    fi
    if [[ "$(grep mastersalt $CONF_PREFIX/grains &>/dev/null |wc -l)" != "0" ]];then
        bs_log "Cleanup old salt grains"
        sed -re "/mastersalt/d" -i $CONF_PREFIX/grains
        salt_call_wrapper --local saltutil.sync_grains
    fi
}

cleanup_old_installs
set_vars
recap
setup_and_maybe_update_code
setup_virtualenv
install_buildouts
create_salt_skeleton
install_salt_envs
maybe_install_projects
exit 0
# vim:set et sts=5 ts=4 tw=0:

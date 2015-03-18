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
#
# Toubleshooting:
# - If the script fails, just relaunch it and it will continue where it was
# - You can safely relaunch it but be ware that it kills the salt daemons upon configure & setup
#   and consequently not safe for putting directly in salt states (with a cmd.run).
#

get_abspath() {
    PYTHON="$(which python 2>/dev/null)"
    if [ ! -f "${PYTHON}" ];then
        cd "$(dirname ${THIS})"
        echo "${PWD}"
        cd - > /dev/null
    else
        "${PYTHON}" << EOF
import os
print os.path.abspath("${THIS}")
EOF
    fi
}

# be sure to have a populated base path
THIS="${0}"
LAUNCH_ARGS=${@}
DNS_RESOLUTION_FAILED="dns resolution failed"
ERROR_MSG="There were errors"
RED="\\e[0;31m"
CYAN="\\e[0;36m"
YELLOW="\\e[0;33m"
NORMAL="\\e[0;0m"
SALT_BOOT_DEBUG="${SALT_BOOT_DEBUG:-}"
SALT_BOOT_DEBUG_LEVEL="${SALT_BOOT_DEBUG_LEVEL:-all}"
ALIVE_MARKER="/tmp/mastersalt_alive"
VALID_BRANCHES=""
PATH="${PATH}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"
if [ -h "${THIS}" ];then
    THIS="$(readlink ${THIS})"
fi
THIS="$(get_abspath ${THIS})"
export PATH

is_lxc() {
    echo  "$(cat -e /proc/1/environ |grep container=lxc|wc -l|sed -e "s/ //g")"
}

set_progs() {
    SED=$(which sed)
    if [ "x${UNAME}" != "xlinux" ];then
        SED=$(which gsed)
    fi
    GETENT="$(which getent 2>/dev/null)"
    PERL="$(which perl 2>/dev/null)"
    PYTHON="$(which python2.7 2>/dev/null)"
    if [ "x${PYTHON}" = "x" ];then
        PYTHON="$(which python 2>/dev/null)"
    fi
    BHOST="$(which host 2>/dev/null)"
    DIG="$(which dig 2>/dev/null)"
    NSLOOKUP="$(which nslookup 2>/dev/null)"
    lxc_ps=$(which lxc-ps 1>/dev/null 2>/dev/null)
    if [ "x$(egrep "^container=" /proc/1/environ|wc -l|sed -e "s/ //g")" = "x0" ];then
        # we are in a container !
        lxc_ps=""
    fi
    if [ "x${lxc_ps}" != "x" ];then
        PS="$lxc_ps --host --"
    else
        PS="$(which ps)"
    fi
    export SED GETENT PERL PYTHON DIG NSLOOKUP PS
}

bs_log(){
    printf "${RED}[bs] ${@}${NORMAL}\n";
}

bs_yellow_log(){
    printf "${YELLOW}[bs] ${@}${NORMAL}\n";
}

debug_msg() {
    if [ "x$SALT_BOOT_DEBUG" != "x" ];then
        bs_log ${@}
    fi
}

# 1: connection failure
# 0: connection success
check_connectivity() {
    ip=${1}
    tempo="${3:-1}"
    port=${2}
    NC=$(which nc 2>/dev/null)
    NETCAT=$(which netcat 2>/dev/null)
    ret="0"
    if [ ! -e "${NC}" ];then
        if [ -e "${NETCAT}" ];then
            NC=${NETCAT}
        fi
    fi
    if [ -e "${NC}" ];then
        while [ "x${tempo}" != "x0" ];do
            tempo="$((${tempo} - 1))"
            # one of
            # Connection to 127.0.0.1 4506 port [tcp/*] succeeded!
            # devhost4.local [127.0.0.1] 4506 (?) open
            test "$(${NC} -w 5 -v -z ${ip} ${port} 2>&1|egrep "open$|Connection.*succeeded"|wc -l|sed -e "s/ //g")" != "0";
            ret="${?}"
            if [ "x${ret}" = "x0" ];then
                break
            fi
            sleep 1
        done
    fi
    echo ${ret}
}

warn_log() {
    if [ -e "${SALT_BOOT_CMDFILE}" ] \
        || [ -e "${SALT_BOOT_OUTFILE}" ] \
        || [ -e "${SALT_BOOT_LOGFILE}" ];\
    then
        bs_log "logs for salt executions availables in:"
        if [ -e "${SALT_BOOT_OUTFILE}" ];then
            bs_log "    - ${SALT_BOOT_OUTFILE}"
        fi
        if [ -e "${SALT_BOOT_LOGFILE}" ];then
            bs_log "    - ${SALT_BOOT_LOGFILE}"
        fi
        if [ -e "${SALT_BOOT_CMDFILE}" ];then
            bs_log "    - ${SALT_BOOT_CMDFILE}"
        fi
        travis_log
    fi
}

travis_log() {
    if [ "x${SALT_NODETYPE}" = "xtravis" ];then
        cat "${SALT_BOOT_OUTFILE}"
        cat "${SALT_BOOT_LOGFILE}"
        cat "${SALT_BOOT_CMDFILE}"
    fi
}

die_() {
    warn_log
    ret=${1}
    shift
    printf "${CYAN}PROBLEM DETECTED, BOOTSALT FAILED${NORMAL}\n" 1>&2
    echo "${@}" 1>&2
    exit $ret
}

die() {
    die_ 1 ${@}
}

die_in_error_() {
    ret=${1}
    shift
    msg="${@:-"$ERROR_MSG"}"
    if [ "x${ret}" != "x0" ];then
        die_ "${ret}" "${msg}"
    fi
}

die_in_error() {
    die_in_error_ "${?}" "${@}"
}

test_online() {
    ping -W 10 -c 1 8.8.8.8 1>/dev/null 2>/dev/null
    echo "${?}"|"${SED}" -e "s/^\(.\).*/\1/g"
}

dns_resolve() {
    ahost="${1}"
    resolvers="hostsv4 hostsv6"
    for i in\
        "${GETENT}"\
        "${PERL}"\
        "${PYTHON}"\
        "${BHOST}"\
        "${NSLOOKUP}"\
        "${DIG}";\
    do
        if [ "x${i}" != "x" ];then
            resolvers="${resolvers} ${i}"
        fi
    done
    if [ "x${resolvers}" = "x" ];then
        die "${DNS_RESOLUTION_FAILED}"
    fi
    res=""
    for resolver in ${resolvers};do
        if [ "x$(echo ${resolver} | grep -q hostsv4;echo "${?}")" = "x0" ];then
            res=$(${GETENT} ahostsv4 ${ahost}|head -n1 2>/dev/null| awk '{ print $1 }')
        elif [ "x$(echo ${resolver} | grep -q hostsv6;echo "${?}")" = "x0" ];then
            res=$(${GETENT} ahostsv6 ${ahost}|head -n1 2>/dev/null| awk '{ print $1 }')
        elif [ "x$(echo ${resolver} | grep -q dig;echo "${?}")" = "x0" ];then
            res=$(${resolver} ${ahost} 2>/dev/null| awk '/^;; ANSWER SECTION:$/ { getline ; print $5 }')
        elif [ "x$(echo ${resolver} | grep -q nslookup;echo "${?}")" = "x0" ];then
            res=$(${resolver} ${ahost} 2>/dev/null| awk '/^Address: / { print $2  }')
        elif [ "x$(echo ${resolver} | grep -q python;echo "${?}")" = "x0" ];then
            res=$(${resolver} -c "import socket;print socket.gethostbyname('${ahost}')" 2>/dev/null)
        elif [ "x$(echo ${resolver} | grep -q perl;echo "${?}")" = "x0" ];then
            res=$(${resolver} -e "use Socket;\$packed_ip=gethostbyname(\"${ahost}\");print inet_ntoa(\$packed_ip)")
        elif [ "x$(echo ${resolver} | grep -q getent;echo "${?}")" = "x0" ];then
            res=$(${resolver} ahosts ${ahost}|head -n1 2>/dev/null| awk '{ print $1 }')
        fi
        # do not accet ipv6 resolutions
        thistest="$(echo "${res}"|grep -q ":";echo ${?})"
        if [ "x${thistest}" = "x0" ];then res="";fi
        if [ "x${res}" != "x" ];then
            break
        fi
    done
    if [ "x${res}" = "x" ];then
        die "${DNS_RESOLUTION_FAILED}"
    fi
    echo ${res}
}

detect_os() {
    # make as a function to be copy/pasted as-is in multiple scripts
    UNAME="$(uname | awk '{print tolower($1)}')"
    IS_UBUNTU=""
    IS_DEBIAN=""
    if [ -e "${CONF_ROOT}/lsb-release" ];then
        . ${CONF_ROOT}/lsb-release
        if [ "x${DISTRIB_CODENAME}" = "xlucid" ]\
            || [ "x${DISTRIB_CODENAME}" = "xmaverick" ]\
            || [ "x${DISTRIB_CODENAME}" = "xnatty" ]\
            || [ "x${DISTRIB_CODENAME}" = "xoneiric" ]\
            || [ "x${DISTRIB_CODENAME}" = "xprecise" ]\
            || [ "x${DISTRIB_CODENAME}" = "xquantal" ]\
            ;then
            EARLY_UBUNTU=y
            BEFORE_RARING=y
        fi
        if [ "x${DISTRIB_CODENAME}" = "xraring" ] || [ "x${EARLY_UBUNTU}" != "x" ];then
            BEFORE_SAUCY="y"
        fi
        if [ "x${DISTRIB_ID}" = "xUbuntu" ];then
            IS_UBUNTU="y"
        fi
    fi
    if [ -e "${CONF_ROOT}/os-release" ];then
        OS_RELEASE_ID=$(egrep ^ID= ${CONF_ROOT}/os-release|"${SED}" -e "s/ID=//g")
        OS_RELEASE_NAME=$(egrep ^NAME= ${CONF_ROOT}/os-release|"${SED}" -e "s/NAME=""//g")
        OS_RELEASE_VERSION=$(egrep ^VERSION= ${CONF_ROOT}/os-release|"${SED}" -e "s/VERSION=/""/g")
        OS_RELEASE_PRETTY_NAME=$(egrep ^PRETTY_NAME= ${CONF_ROOT}/os-release|"${SED}" -e "s/PRETTY_NAME=""//g")

    fi
    if [ -e "${CONF_ROOT}/debian_version" ] && [ "x${OS_RELEASE_ID}" = "xdebian" ] && [ "x${DISTRIB_ID}" != "xUbuntu" ];then
        IS_DEBIAN="y"
        SALT_BOOT_OS="debian"
        # Debian GNU/Linux 7 (wheezy) -> wheezy
        DISTRIB_CODENAME="$(echo ${OS_RELEASE_PRETTY_NAME} | "${SED}" -e "s/.*(\\(.*\\)).*/\1/g")"
    fi
    DEBIAN_VERSION=$(cat /etc/debian_version 2>/dev/null)
    if [ -e "${CONF_ROOT}/debian_version" ];then
        IS_DEBIAN="y"
        SALT_BOOT_OS="debian"
        # Debian GNU/Linux 7 (wheezy) -> wheezy
        if grep -q lenny /etc/apt/sources.list 2>/dev/null;then
            DISTRIB_CODENAME="lenny"
        fi
    fi
    if [ "x${DISTRIB_CODENAME}" = "xlenny" ];then
        export CFLAGS="-I/usr/local/include" LDFLAGS="-L/usr/local/lib"
    fi
    if [ "x${IS_UBUNTU}" != "x" ];then
        SALT_BOOT_OS="ubuntu"
        DISTRIB_NEXT_RELEASE="saucy"
        DISTRIB_BACKPORT="${DISTRIB_NEXT_RELEASE}"
        IS_DEBIAN=""
    elif [ "x${IS_DEBIAN}" != "x" ];then
        if [ "x${DISTRIB_CODENAME}"  = "xwheezy" ];then
            DISTRIB_NEXT_RELEASE="jessie"
        elif [ "x${DISTRIB_CODENAME}"  = "xsqueeze" ];then
            DISTRIB_NEXT_RELEASE="wheezy"
        fi
        DISTRIB_BACKPORT="wheezy-backports"
    fi

}

get_module_args() {
    arg=""
    for i in ${@};do
        arg="${arg} -m \"${i}/_modules\""
    done
    echo ${arg}
}

interactive_tempo(){
    if [ "x${SALT_REATTACH}" = "x" ];then
        tempo="${@}"
        tempo_txt="$tempo"
        if [ -f "${PYTHON}" ] && [ $tempo_txt -ge 60 ];then
            tempo_txt="$(python -c "print $tempo / 60") minute(s)"
        else
            tempo_txt="$tempo second(s)"
        fi
        bs_yellow_log "The installation will continue in $tempo_txt"
        bs_yellow_log "unless you press enter to continue or C-c to abort"
        bs_yellow_log "-------------------  ????  -----------------------"
        read -t $tempo
        bs_yellow_log "Continuing..."
    fi
}

get_chrono() {
    date "+%F_%H-%M-%S"
}

get_full_chrono() {
    date "+%F_%H-%M-%S-%N"
}

set_colors() {
    if [ "x${NO_COLORS}" != "x" ];then
        YELLOW=""
        RED=""
        CYAN=""
        NORMAL=""
    fi
}

get_local_mastersalt_mode() {
    default_mode="remote"
    mastersalt_mode="$(get_conf local_mastersalt_mode)"
    if [ "x${FORCE_LOCAL_SALT_MODE}" != "x" ];then
        mastersalt_mode="${FORCE_LOCAL_SALT_MODE}"
    fi
    thistest="$(echo "${mastersalt_mode}"|egrep -q '^(remote|masterless)$';echo "${?}")"
    if [ "x${thistest}" != "x0" ];then
        mastersalt_mode="${default_mode}"
    fi
    store_conf local_mastersalt_mode "${mastersalt_mode}"
    echo "${mastersalt_mode}"
}

get_local_salt_mode() {
    default_mode="masterless"
    salt_mode="$(get_conf local_salt_mode)"
    if [ "x${FORCE_LOCAL_SALT_MODE}" != "x" ];then
        salt_mode="${FORCE_LOCAL_SALT_MODE}"
    fi
    thistest="$(echo "${salt_mode}"|egrep -q '^(remote|masterless)$';echo "${?}")"
    if [ "x${thistest}" != "x0" ];then
        salt_mode="${default_mode}"
    fi
    store_conf local_salt_mode "${salt_mode}"
    echo "${salt_mode}"
}

get_minion_id() {
    confdir="${1}"
    force="${3}"
    notfound=""
    if [ "x$(egrep -q "^id: [^ ]+" /etc/hosts $(find "${confdir}/minion"* -type f 2>/dev/null) 2>/dev/null;echo ${?})" != "x0" ]\
       || [ "$(find ${confdir}/minion* -type f 2>/dev/null|wc -l|sed -e "s/ //g")" ];then
       notfound="y"
    fi
    if [ "x${notfound}" != "x" ] && [ "x${SALT_REATTACH}" != "x" ] && [ -e "${SALT_REATTACH_DIR}/minion" ];then
        mmid="$(egrep "^id:" "${SALT_REATTACH_DIR}/minion"|awk '{print $2}'|sed -e "s/ //")"
    else
        mmid="${2:-$(hostname)}"
        if [ "x${force}" = "x" ];then
            fics=$(find "${confdir}"/minion* -type f 2>/dev/null)
            if [ "x${fics}" != "x" ];then
                mmid=$(egrep -r "^id:" $(find "${confdir}"/minion* -type f 2>/dev/null|grep -v sed) 2>/dev/null|awk '{print $2}'|head -n1)
            fi
            if [ "x${mmid}" = "x" ] && [ -f "${confdir}/minion_id" ];then
                mmid=$(cat "${confdir}/minion_id" 2> /dev/null)
            fi
            if [ "x${mmid}" = "x" ] && [ -f "${CONF_PREFIX}/minion_id" ];then
                mmid=$(cat "${CONF_PREFIX}/minion_id" 2> /dev/null)
            fi
        fi
        if [ "x${mmid}" = "x" ];then
            mmid="${2:-$(hostname)}"
        fi
    fi
    if [ "x$(echo "${mmid}"|grep -q '\.';echo ${?})" != "x0" ];then
        mmid="${mmid}.${DEFAULT_DOMAINNAME}"
    fi
    echo $mmid
}

set_valid_upstreams() {
    if [ ! -e "$(which git 2>/dev/null)" ];then
        VALID_BRANCHES="master stable"
    fi
    if [ "x${VALID_BRANCHES}" = "x" ];then
        if [ "x${SALT_BOOT_LIGHT_VARS}" = "x" ];then
            VALID_BRANCHES="$(echo "$(git ls-remote "${MAKINASTATES_URL}"|grep "refs/heads"|awk -F/ '{print $3}'|grep -v HEAD)")"
        fi
        if [ -e "${SALT_MS}" ];then
            VALID_BRANCHES="${VALID_BRANCHES} $(echo $(cd "${SALT_MS}" && git branch| cut -c 3-))"
        fi
        if [ -e "${MASTERSALT_MS}" ];then
            VALID_BRANCHES="${VALID_BRANCHES} $(echo $(cd "${MASTERSALT_MS}" && git branch| cut -c 3-))"
        fi
    fi
    # if we pin a particular changeset make hat as a valid branch
    # also add if we had a particular changeset saved in conf
    for msb in "${MS_BRANCH}" "$(get_conf branch)";do
        thistest="$(echo "${msb}" | grep -q "changeset:";echo "${?}")"
        if [ "x${thistest}" = "x0" ];then
            ch="$(echo "${msb}"|${SED} -e "s/changeset://g")"
            if [ "x$(git log "$ch" | wc -l|sed -e "s/ //g")"  != "x0" ];then
                VALID_BRANCHES="${VALID_BRANCHES} ${ch} changeset:$ch"
            fi
        fi
    done
    # remove \n
    VALID_BRANCHES=$(echo "${VALID_BRANCHES}")
}


get_conf_root() {
    conf_root="${CONF_ROOT:-"/etc"}"
    if [ "x${conf_root}" = "x" ];then
        conf_root="/etc"
    fi
    echo $conf_root
}

get_conf(){
    key="${1}"
    conf_root="$(get_conf_root)"
    echo $(cat "${conf_root}/makina-states/$key" 2>/dev/null)
}

store_conf(){
    key="${1}"
    val="${2}"
    conf_root="$(get_conf_root)"
    if [ ! -d "${conf_root}/makina-states" ];then
        mkdir -pv "${conf_root}/makina-states"
    fi
    echo "${val}">"${conf_root}/makina-states/${key}"
}

set_conf() {
    store_conf "${@}"
}

get_ms_branch() {
    get_ms_branch_branch="${MS_BRANCH}"
    # verify that the requested branch OR changeset exists
    thistest="$(echo "${VALID_BRANCHES}" | grep -q "${get_ms_branch_branch}";echo "${?}")"
    if [ "x${thistest}" = "x0" ];then
        branch=""
    fi
    if [ "x${FORCE_MS_BRANCH}" = "x" ];then
        savedbranch="$(get_conf branch)"
        thistest="$(echo "${VALID_BRANCHES}"|grep -q "${savedbranch}";echo "${?}")"
        if [ "x${savedbranch}" != "x" ] && [ "x${thistest}" = "x0" ];then
            get_ms_branch_branch="${savedbranch}"
        fi
    fi
    echo "${get_ms_branch_branch}"
}

get_bootsalt_mode() {
    bootsalt_mode="$(get_conf bootsalt_mode)"
    if [ "x${bootsalt_mode}" = "x" ];then
        if [ "x${IS_MASTERSALT}" != "x" ];then
            bootsalt_mode="mastersalt"
        else
            bootsalt_mode="salt"
        fi
    fi
    echo "${bootsalt_mode}"
}

get_salt_nodetype() {
    default_nodetype="server"
    if [ "x$(is_lxc)" != "x0" ];then
        default_nodetype="lxccontainer"
    fi
    if [ "x${FORCE_SALT_NODETYPE}" != "x" ];then
        default_nodetype=""
    fi
    nodetype="${SALT_NODETYPE:-${1:-$default_nodetype}}"
    # verify that the requested branch exists
    if [ "x${FORCE_SALT_NODETYPE}" = "x" ];then
        savednodetype="$(get_conf nodetype)"
        if [ "x${savednodetype}" != "x" ];then
            nodetype="${savednodetype}"
        fi
    fi
    if [ "x${nodetype}" != "x" ];then
        if [ -e "${SALT_MS}" ];then
            if [ ! -e "${SALT_MS}/nodetypes/${nodetype}.sls" ];then
                # invalid nodetype
                nodetype=""
            else
                store_conf nodetype "${nodetype}"
            fi
        fi
    fi
    echo "${nodetype}"
}

set_vars() {
    set_colors
    if [ "x$(echo "${LAUNCH_ARGS}" | grep -q reattach;echo ${?})" = "x0" ]\
        || [ "x$(echo "${LAUNCH_ARGS}" | grep -q from-salt-cloud;echo ${?})" = "x0" ];then
        SALT_REATTACH="1"
    else
        SALT_REATTACH="${SALT_REATTACH:-}"
    fi
    LOCAL_SALT_MODE="$(get_local_salt_mode)"
    DEFAULT_DOMAINNAME="local"
    HOST="$(hostname -f)"
    if [ $(hostname -f|sed -e "s/\./\.\n/g"|grep -c "\.") -ge 2 ];then
        DEFAULT_DOMAINNAME="$(hostname -f|sed -re "s/[^.]+\.(.*)/\1/g")"
        HOST="$(hostname -f|sed -re "s/([^.]+)\.(.*)/\1/g")"
    fi
    SALT_BOOT_LOCK_FILE="/tmp/boot_salt_sleep-$(get_full_chrono)"
    LAST_RETCODE_FILE="/tmp/boot_salt_rc-$(get_full_chrono)"
    QUIET=${QUIET:-}
    ROOT="${ROOT:-"/"}"
    CONF_ROOT="${CONF_ROOT:-"${ROOT}etc"}"
    ETC_INIT="${ETC_INIT:-"${CONF_ROOT}/init"}"
    CHRONO="$(get_chrono)"
    TRAVIS_DEBUG="${TRAVIS_DEBUG:-}"
    VENV_REBOOTSTRAP="${VENV_REBOOTSTRAP:-}"
    ONLY_BUILDOUT_REBOOTSTRAP="${ONLY_BUILDOUT_REBOOTSTRAP:-}"
    BUILDOUT_REBOOTSTRAP="${BUILDOUT_REBOOTSTRAP:-${VENV_REBOOTSTRAP}}"
    SALT_REBOOTSTRAP="${SALT_REBOOTSTRAP:-${VENV_REBOOTSTRAP}}"
    BASE_PACKAGES=""
    BASE_PACKAGES="$BASE_PACKAGES libmemcached-dev acl build-essential m4 libtool pkg-config autoconf gettext bzip2"
    BASE_PACKAGES="$BASE_PACKAGES groff man-db automake libsigc++-2.0-dev tcl8.5 python-dev"
    if [ "x${DISTRIB_CODENAME}" != "xlenny" ];then
        BASE_PACKAGES="$BASE_PACKAGES libyaml-dev python2.7 python2.7-dev"
        BASE_PACKAGES="$BASE_PACKAGES libzmq3-dev"
    fi
    BASE_PACKAGES="$BASE_PACKAGES swig libssl-dev debconf-utils python-virtualenv"
    BASE_PACKAGES="$BASE_PACKAGES vim git rsync"
    BASE_PACKAGES="$BASE_PACKAGES libgmp3-dev"
    BASE_PACKAGES="$BASE_PACKAGES libffi-dev"
    BRANCH_PILLAR_ID="makina-states.salt.makina-states.rev"
    MAKINASTATES_TEST=${MAKINASTATES_TEST:-}
    SALT_BOOT_INITIAL_HIGHSTATE="${SALT_BOOT_INITIAL_HIGHSTATE:-}"
    IS_SALT_UPGRADING="${IS_SALT_UPGRADING:-}"
    IS_SALT="${IS_SALT:-y}"
    IS_SALT_MASTER="${IS_SALT_MASTER:-y}"
    IS_SALT_MINION="${IS_SALT_MINION:-y}"
    IS_MASTERSALT="${IS_MASTERSALT:-}"
    IS_MASTERSALT_MASTER="${IS_MASTERSALT_MASTER:-}"
    IS_MASTERSALT_MINION="${IS_MASTERSALT_MINION:-}"
    MAKINASTATES_URL="${MAKINASTATES_URL:-"https://github.com/makinacorpus/makina-states.git"}"
    DEFAULT_MS_BRANCH="master"
    if [ "x${TRAVIS}" != "x" ];then
        DEFAULT_MS_BRANCH="changeset:$(git log|head -n1|awk '{print $2}')"
    fi
    MS_BRANCH="${MS_BRANCH:-${DEFAULT_MS_BRANCH}}"
    FORCE_MS_BRANCH="${FORCE_MS_BRANCH:-""}"
    PREFIX="${PREFIX:-${ROOT}srv}"
    BIN_DIR="${BIN_DIR:-${ROOT}usr/bin}"
    SALT_PILLAR="${SALT_PILLAR:-$PREFIX/pillar}"
    SALT_BOOT_SYNC_CODE="${SALT_BOOT_SYNC_CODE:-}"
    SALT_BOOT_NOCONFIRM="${SALT_BOOT_NOCONFIRM:-}"
    SALT_ROOT="${SALT_ROOT:-$PREFIX/salt}"
    SALT_BOOT_OUTFILE="${SALT_MS}/.boot_salt.$(get_chrono).out"
    SALT_BOOT_LOGFILE="${SALT_MS}/.boot_salt.$(get_chrono).log"
    SALT_MS="${SALT_ROOT}/makina-states"
    MASTERSALT_PILLAR="${MASTERSALT_PILLAR:-$PREFIX/mastersalt-pillar}"
    MASTERSALT_ROOT="${MASTERSALT_ROOT:-$PREFIX/mastersalt}"
    MASTERSALT_MS="${MASTERSALT_ROOT}/makina-states"
    TMPDIR="${TMPDIR:-"/tmp"}"
    VENV_PATH="${VENV_PATH:-"/salt-venv"}"
    EGGS_GIT_DIRS="docker-py m2crypto salt salttesting"
    PIP_CACHE="${VENV_PATH}/cache"
    SALT_VENV_PATH="${VENV_PATH}/salt"
    MASTERSALT_VENV_PATH="${VENV_PATH}/mastersalt"
    CONF_PREFIX="${CONF_PREFIX:-"${CONF_ROOT}/salt"}"
    MCONF_PREFIX="${MCONF_PREFIX:-"${CONF_ROOT}/mastersalt"}"
    # global installation marker
    SALT_BOOT_NOW_INSTALLED=""
    # the current mastersalt.makinacorpus.net hostname
    MASTERSALT_MAKINA_DNS="mastersalt.makina-corpus.net"
    BOOT_LOGS="${SALT_MS}/.bootlogs"
    MBOOT_LOGS="${MASTERSALT_MS}/.bootlogs"
    # base sls bootstrap
    bootstrap_pref="makina-states.bootstraps"
    bootstrap_nodetypes_pref="${bootstrap_pref}.nodetypes"
    bootstrap_controllers_pref="${bootstrap_pref}.controllers"
    set_valid_upstreams

    # nodetypes (calculed now in get_salt_nodetype) and controllers sls
    SALT_MASTER_CONTROLLER_DEFAULT="salt_master"
    SALT_MASTER_CONTROLLER_INPUTED="${SALT_MASTER_CONTROLLER}"
    SALT_MASTER_CONTROLLER="${SALT_MASTER_CONTROLLER:-$SALT_MASTER_CONTROLLER_DEFAULT}"
    SALT_MINION_CONTROLLER_DEFAULT="salt_minion"
    SALT_MINION_CONTROLLER_INPUTED="${SALT_MINION_CONTROLLER}"
    SALT_MINION_CONTROLLER="${SALT_MINION_CONTROLLER:-$SALT_MINION_CONTROLLER_DEFAULT}"
    SALT_LIGHT_INSTALL=""
    NICKNAME_FQDN="$(get_minion_id)"
    if [ "x$(echo "${NICKNAME_FQDN}"|grep -q \.;echo ${?})" = "x0" ];then
        DOMAINNAME="$(echo "${NICKNAME_FQDN}"|${SED} -e "s/^[^.]*\.//g")"
    else
        DOMAINNAME="${DEFAULT_DOMAINNAME}"
        NICKNAME_FQDN="${HOST}.${DOMAINNAME}"
        set_dns
    fi

    # select the daemons to install but also
    # detect what is already present on the system
    if [ "x${SALT_CONTROLLER}" = "xsalt_master" ]\
     || [ "x$(grep -q "makina-states.controllers.salt_master: true" "${CONF_PREFIX}/grains" 2>/dev/null;echo "${?}")" = "x0" ];then
        IS_SALT_MASTER="y"
    else
        IS_SALT_MINION="y"
    fi
    if [ "x${MASTERSALT_CONTROLLER}" = "xmastersalt_master" ]\
     || [ "x$(grep -q "makina-states.controllers.mastersalt_master: true" "${MCONF_PREFIX}/grains" 2>/dev/null;echo "${?}")" = "x0" ];then
        IS_MASTERSALT_MASTER="y"
    fi
    if [ "x${MASTERSALT_CONTROLLER}" = "xmastersalt_minion" ]\
     || [ "x$(grep -q "makina-states.controllers.mastersalt_minion: true" "${MCONF_PREFIX}/grains" 2>/dev/null;echo "${?}")" = "x0" ];then
        IS_MASTERSALT_MINION="y"
    fi
    if [ "x${MASTERSALT}" != "x" ];then
        IS_MASTERSALT_MINION="y"
    fi
    if [ -e "${ETC_INIT}/salt-master.conf" ]\
        || [ -e "${ETC_INIT}.d/salt-master" ]\
        || [ "x${IS_SALT_MASTER}" != "x" ];then
        IS_SALT="y"
        IS_SALT_MASTER="y"
        IS_SALT_MINION="y"
    fi
    if [ -e "${ETC_INIT}/salt-minion.conf" ]\
        || [ -e "${ETC_INIT}.d/salt-minion" ]\
        || [ "x${IS_SALT_MINION}" != "x" ];then
        IS_SALT="y"
        IS_SALT_MINION="y"
    fi
    MASTERSALT_INIT_PRESENT=""
    # when we come from salt cloud, will never have to
    # test for mastersalt, it is explictly set
    if [ "x${SALT_REATTACH}" != "x" ];then
        if [ "x${SALT_REATTACH_DIR}" = "x" ] || [ ! -e "${SALT_REATTACH_DIR}" ] ;then
            if [ "x$(echo "${0}"|${SED} -e "s/.*saltcloud.*/match/g")" = "xmatch" ];then
                SALT_REATTACH_DIR="${SALT_REATTACH_DIR:-"$(dirname ${0})"}"
            else
                echo "Invalid --reattach-dir: ${SALT_REATTACH_DIR}"
                exit
            fi
        fi
    fi
    # the mastersalt mode is forced for minions linked via salt-cloud/seed
    # and for others, we test the presence of the init scripts
    if [ "x${SALT_REATTACH}" = "x" ];then
        if [ -e "${ETC_INIT}.d/mastersalt-master" ]\
            || [ -e "${ETC_INIT}/mastersalt-master.conf" ]\
            || [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            MASTERSALT_INIT_MASTER_PRESENT="y"
            MASTERSALT_INIT_PRESENT="y"
        fi
        if [ -e "${ETC_INIT}.d/mastersalt-minion" ]\
            || [ -e "${ETC_INIT}/mastersalt-minion.conf" ]\
            || [ "x${IS_MASTERSALT_MINION}" != "x" ];then
            MASTERSALT_INIT_MINION_PRESENT="y"
            MASTERSALT_INIT_PRESENT="y"
        fi
    fi
    if [ "x${MASTERSALT_INIT_PRESENT}" != "x" ];then
        IS_MASTERSALT="y"
    fi
    if [ "x${MASTERSALT_INIT_MASTER_PRESENT}" != "x" ];then
        IS_MASTERSALT_MASTER="y"
    fi
    if [ "x${MASTERSALT_INIT_MINION_PRESENT}" != "x" ];then
        IS_MASTERSALT_MINION="y"
    fi
    if [ "x${SALT_REATTACH}" != "x" ];then
        if [ "x${FORCE_IS_MASTERSALT_MINION}" = "xyes" ];then
            store_conf bootsalt_mode mastersalt
            FORCE_IS_SALT="yes"
            FORCE_IS_MASTERSALT="no"
            FORCE_IS_MASTERSALT_MINION="yes"
        else
            store_conf bootsalt_mode salt
            FORCE_IS_MASTERSALT="no"
            FORCE_IS_SALT="no"
            FORCE_IS_SALT_MASTER="no"
            FORCE_IS_SALT_MINION="yes"
        fi
    fi
    if  [ "x$(get_bootsalt_mode)" = "xmastersalt" ]\
        ||  [ "x${IS_MASTERSALT_MINION}" != "x" ];then
        IS_MASTERSALT="y"
        IS_MASTERSALT_MINION="y"
    fi
    if [ "x${FORCE_IS_SALT}" = "xno" ];then
        IS_SALT=""
        IS_SALT_MASTER=""
        IS_SALT_MINION=""
    fi
    if [ "x${FORCE_IS_MASTERSALT}" = "xno" ];then
        IS_MASTERSALT=""
        IS_MASTERSALT_MASTER=""
        IS_MASTERSALT_MINION=""
    fi
    if [ "x${FORCE_IS_SALT_MASTER}" = "xno" ];then
        IS_SALT=""
        IS_SALT_MASTER=""
    fi
    if [ "x${FORCE_IS_SALT_MINION}" = "xno" ];then
        IS_SALT=""
        IS_SALT_MINION=""
    fi
    if [ "x${FORCE_IS_MASTERSALT_MASTER}" = "xno" ];then
        IS_MASTERSALT=""
        IS_MASTERSALT_MASTER=""
    fi
    if [ "x${FORCE_IS_MASTERSALT_MINION}" = "xno" ];then
        IS_MASTERSALT=""
        IS_MASTERSALT_MINION=""
    fi
    if [ "x${FORCE_IS_SALT}" = "xyes" ];then
        IS_SALT="y"
        IS_SALT_MASTER="y"
        IS_SALT_MINION="y"
    fi
    if [ "x${FORCE_IS_MASTERSALT}" = "xyes" ];then
        IS_MASTERSALT="y"
        IS_MASTERSALT_MASTER="y"
        IS_MASTERSALT_MINION="y"
    fi
    if [ "x${FORCE_IS_SALT_MASTER}" = "xyes" ];then
        IS_SALT="y"
        IS_SALT_MASTER="y"
    fi
    if [ "x${FORCE_IS_SALT_MINION}" = "xyes" ];then
        IS_SALT="y"
        IS_SALT_MINION="y"
    fi
    if [ "x${FORCE_IS_MASTERSALT_MASTER}" = "xyes" ];then
        IS_MASTERSALT="y"
        IS_MASTERSALT_MASTER="y"
    fi
    if [ "x${FORCE_IS_MASTERSALT_MINION}" = "xyes" ];then
        IS_MASTERSALT="y"
        IS_MASTERSALT_MINION="y"
    fi
    # force mode (via cmdline)
    if [ "x${IS_SALT_MINION}" = "x" ] && [ "x${IS_SALT_MASTER}" = "x" ];then
        IS_SALT=""
    fi
    if [ "x${IS_MASTERSALT_MINION}" = "x" ] && [ "x${IS_MASTERSALT_MASTER}" = "x" ];then
        IS_MASTERSALT=""
    fi

    MASTERSALT_MASTER_IP="${MASTERSALT_MASTER_IP:-"0.0.0.0"}"
    MASTERSALT_MINION_IP="${MASTERSALT_MINION_IP:-"127.0.0.1"}"
    # mastersalt variables
    if [ "x${IS_MASTERSALT}" != "x" ];then
        MASTERSALT_MASTER_CONTROLLER_DEFAULT="mastersalt_master"
        MASTERSALT_MASTER_CONTROLLER_INPUTED="${MASTERSALT_MASTER_CONTROLLER}"
        MASTERSALT_MASTER_CONTROLLER="${MASTERSALT_MASTER_CONTROLLER:-${MASTERSALT_MASTER_CONTROLLER_DEFAULT}}"
        MASTERSALT_MINION_CONTROLLER_DEFAULT="mastersalt_minion"
        MASTERSALT_MINION_CONTROLLER_INPUTED="${MASTERSALT_MINION_CONTROLLER}"
        MASTERSALT_MINION_CONTROLLER="${MASTERSALT_MINION_CONTROLLER:-${MASTERSALT_MINION_CONTROLLER_DEFAULT}}"
        MASTERSALT_INPUTED="${MASTERSALT}"
        # host running the mastersalt salt-master
        if [ "x${SALT_REATTACH}" != "x" ] && [ -e "${SALT_REATTACH_DIR}/minion" ];then
             MASTERSALT="$(egrep "^master:" "${SALT_REATTACH_DIR}"/minion 2>/dev/null|awk '{print $2}'|${SED} -e "s/ //")"
             MASTERSALT_MASTER_DNS="${MASTERSALT}"
             MASTERSALT_MASTER_IP="${MASTERSALT}"
             MASTERSALT_MASTER_PORT="$(egrep "^master_port:" "${SALT_REATTACH_DIR}"/minion|awk '{print $2}'|${SED} -e "s/ //")"
        fi
        if [ "x${SALT_REATTACH}" = "x" ] && [ -e "${MASTERSALT_PILLAR}/mastersalt.sls" ];then
            PMASTERSALT="$(grep "master: " ${MASTERSALT_PILLAR}/mastersalt.sls |awk '{print $2}'|tail -n 1|${SED} -e "s/ //g")"
            if [ "x${PMASTERSALT}" != "x" ];then
                MASTERSALT="${PMASTERSALT}"
            fi
        fi
        for i in /etc/mastersalt/minion /etc/mastersalt/minion.d/00_global.conf;do
            if [ "x${MASTERSALT}" = "x" ] && [ -e "${i}" ];then
                PMASTERSALT="$(egrep "^master: " ${i} |awk '{print $2}'|tail -n 1|${SED} -e "s/ //g")"
                if [ "x${PMASTERSALT}" != "x" ];then
                    MASTERSALT="${PMASTERSALT}"
                    break
                fi
            fi
        done
        if [ "x${MASTERSALT}" = "x" ] && [ "x${IS_MASTERSALT_MASTER}" ];then
            MASTERSALT="${NICKNAME_FQDN}"
            MASTERSALT_MASTER_DNS="${NICKNAME_FQDN}"
        fi

        MASTERSALT_MASTER_DNS="${MASTERSALT_MASTER_DNS:-${MASTERSALT}}"
        MASTERSALT_MASTER_PORT="${MASTERSALT_MASTER_PORT:-"${MASTERSALT_PORT:-"4606"}"}"
        MASTERSALT_MASTER_PUBLISH_PORT="$(( ${MASTERSALT_MASTER_PORT} - 1 ))"

        MASTERSALT_MINION_DNS="${MASTERSALT_MINION_DNS:-"localhost"}"
        MASTERSALT_MINION_ID="$(get_minion_id)"

        if [ "x${MASTERSALT_MASTER_IP}" = "x127.0.0.1" ];then
            MASTERSALT_MASTER_DNS="localhost"
        fi
        if [ "x${MASTERSALT_MINION_IP}" = "x127.0.0.1" ];then
            MASTERSALT_MINION_DNS="localhost"
        fi

        if [ "x${MASTERSALT_MASTER_IP}" = "x" ];then
            die "MASTERSALT MASTER: invalid dns: ${MASTERSALT_MASTER_DNS}"
        fi
        if [ "x${MASTERSALT_MINION_IP}" = "x" ];then
            die "MASTERSALT MINION: invalid dns: ${MASTERSALT_MINION_DNS}"
        fi

        mastersalt_bootstrap_nodetype="${bootstrap_nodetypes_pref}.$(get_salt_nodetype)"
        mastersalt_bootstrap_master="${bootstrap_controllers_pref}.${MASTERSALT_MASTER_CONTROLLER}"
        mastersalt_bootstrap_minion="${bootstrap_controllers_pref}.${MASTERSALT_MINION_CONTROLLER}"
    fi
    # salt variables
    SALT_MINION_ID="$(get_minion_id)"
    if [ "x${IS_SALT}" != "x" ];then
        SALT_MASTER_IP_DEFAULT="127.0.0.1"
        SALT_MASTER_DNS_DEFAULT="localhost"
        SALT_MASTER_PORT_DEFAULT="4506"
        set_default_vars=""
        if [ "x${SALT_REATTACH}" != "x" ];then
            if [ "x${IS_MASTERSALT}" = "x" ] && [ -e "${SALT_REATTACH_DIR}/minion" ];then
                SALT_MASTER_DNS_DEFAULT="$(egrep "^master:" "${SALT_REATTACH_DIR}"/minion|awk '{print $2}'|${SED} -e "s/ //")"
                SALT_MASTER_IP_DEFAULT="${SALT_MASTER_DNS_DEFAULT}"
                SALT_MASTER_PORT_DEFAULT="$(egrep "^master_port:" "${SALT_REATTACH_DIR}"/minion|awk '{print $2}'|${SED} -e "s/ //")"
                set_default_vars="x"
            fi
            if [ "x${IS_MASTERSALT}" != "x" ];then
                set_default_vars="x"
            fi
        fi
        if [ "x${set_default_vars}" != "x" ];then
            SALT_MASTER_DNS="${SALT_MASTER_DNS_DEFAULT}"
            SALT_MASTER_IP="${SALT_MASTER_IP_DEFAULT}"
            SALT_MASTER_PORT="${SALT_MASTER_PORT_DEFAULT}"
        fi
        SALT_MASTER_DNS="${SALT_MASTER_DNS:-"${SALT_MASTER_DNS_DEFAULT}"}"
        SALT_MASTER_IP="${SALT_MASTER_IP:-$(dns_resolve ${SALT_MASTER_DNS})}"

        SALT_MASTER_PORT="${SALT_MASTER_PORT:-"${SALT_MASTER_PORT_DEFAULT}"}"
        SALT_MASTER_PUBLISH_PORT="$(( ${SALT_MASTER_PORT} - 1 ))"

        SALT_MINION_DNS="${SALT_MINION_DNS:-"localhost"}"
        SALT_MINION_IP="$(dns_resolve ${SALT_MINION_DNS})"

        if [ "x${SALT_MASTER_IP}" = "x127.0.0.1" ];then
            SALT_MASTER_DNS="localhost"
        fi
        if [ "x${SALT_MINION_IP}" = "x127.0.0.1" ];then
            SALT_MINION_DNS="localhost"
        fi

        if [ "x${SALT_MASTER_IP}" = "x" ];then
            die "SALT MASTER: invalid dns: ${SALT_MASTER_DNS}"
        fi
        if [ "x${SALT_MINION_IP}" = "x" ];then
            die "SALT MINION: invalid dns: ${SALT_MINION_DNS}"
        fi

        salt_bootstrap_nodetype="${bootstrap_nodetypes_pref}.$(get_salt_nodetype)"
        salt_bootstrap_master="${bootstrap_controllers_pref}.${SALT_MASTER_CONTROLLER}"
        salt_bootstrap_minion="${bootstrap_controllers_pref}.${SALT_MINION_CONTROLLER}"
    fi

    if [ "x$(get_ms_branch)" = "x" ] \
        && [ "x${SALT_NODETYPE}" != "xtravis" ];then
        bs_yellow_log "Valid branches: $(echo ${VALID_BRANCHES})"
        die "Please provide a valid \$MS_BRANCH (inputed: "${MS_BRANCH}")"
    fi
    if [ "x$(get_salt_nodetype)" = "x" ];then
        bs_yellow_log "Valid nodetypes $(echo $(ls "${SALT_MS}/nodetypes"|"${SED}" -e "s/.sls//"))"
        die "Please provide a valid nodetype (inputed: "${SALT_NODETYPE_INPUTED}")"
    fi

    # just tell to bootstrap and run highstates
    if [ "x${IS_SALT_UPGRADING}" != "x" ];then
        SALT_BOOT_SKIP_HIGHSTATES=""
        MASTERSALT_BOOT_SKIP_HIGHSTATE=""
        SALT_BOOT_SKIP_CHECKOUTS=""
        SALT_REBOOTSTRAP="y"
        BUILDOUT_REBOOTSTRAP="y"
    fi
    if [ "x${QUIET}" = "x" ];then
        QUIET_GIT=""
    else
        QUIET_GIT="-q"
    fi
    if [ "x${IS_MASTERSALT}" != "x" ];then
        store_conf bootsalt_mode mastersalt
    else
        store_conf bootsalt_mode salt
    fi

    if [ "x$(get_local_salt_mode)" = "xmasterless" ] && [ "x${IS_MASTERSALT}" = "x" ];then
        SALT_LIGHT_INSTALL="y"
    fi


    # export variables to support a restart
    export ONLY_BUILDOUT_REBOOTSTRAP SALT_LIGHT_INSTALL
    export EGGS_GIT_DIRS
    export TRAVIS_DEBUG SALT_BOOT_LIGHT_VARS DO_REFRESH_MODULES
    export IS_SALT_UPGRADING SALT_BOOT_SYNC_CODE SALT_BOOT_INITIAL_HIGHSTATE
    export SALT_REBOOTSTRAP BUILDOUT_REBOOTSTRAP VENV_REBOOTSTRAP
    export MS_BRANCH FORCE_MS_BRANCH
    export IS_SALT IS_SALT_MASTER IS_SALT_MINION
    export IS_MASTERSALT IS_MASTERSALT_MASTER IS_MASTERSALT_MINION
    export FORCE_IS_SALT FORCE_IS_SALT_MASTER FORCE_IS_SALT_MINION
    export FORCE_IS_MASTERSALT FORCE_IS_MASTERSALT_MASTER FORCE_IS_MASTERSALT_MINION
    #
    export SALT_MINION_ID MASTERSALT_MINION_ID
    export FORCE_SALT_MINION_ID FORCE_MASTERSALT_MINION_ID
    #
    export BASE_PACKAGES MAKINASTATES_URL SALT_BOOT_NOCONFIRM
    #
    export MASTERSALT_ROOT SALT_ROOT
    export SALT_PILLAR MASTERSALT_PILLAR
    export MASTERSALT_MS SALT_MS
    #
    export ROOT PREFIX ETC_INIT
    export VENV_PATH CONF_ROOT
    export MASTERSALT_VENV_PATH SALT_VENV_PATH PIP_CACHE
    export MCONF_PREFIX CONF_PREFIX
    #
    export SALT_NODETYPE FORCE_SALT_NODETYPE
    export MASTERSALT_MINION_CONTROLLER MASTERSALT_MASTER_CONTROLLER
    export SALT_MINION_CONTROLLER SALT_MASTER_CONTROLLER
    #
    export SALT_MASTER_IP SALT_MASTER_DNS
    export MAKINASTATES_TEST
    export SALT_MINION_IP SALT_MINION_DNS
    export SALT_MASTER_PORT SALT_MASTER_PUBLISH_PORT
    export MASTERSALT
    export MASTERSALT_MASTER_IP MASTERSALT_MASTER_DNS
    export MASTERSALT_MASTER_PORT MASTERSALT_MASTER_PUBLISH_PORT
    export MASTERSALT_MINION_IP MASTERSALT_MINION_DNS
    #
    export MASTERSALT_BOOT_SKIP_HIGHSTATE SALT_BOOT_SKIP_HIGHSTATE SALT_BOOT_SKIP_HIGHSTATES
    #
    export SALT_REATTACH SALT_REATTACH_DIR
    #
    export yaml_file_changed yaml_added_value yaml_edited_value
    export mastersalt_master_changed mastersalt_minion_challenge
    export salt_master_changed salt_minion_challenge

}

# --------- PROGRAM START

mastersalt_processes() {
    ps aux|grep mastersalt
}

recap_(){
    need_confirm="${1}"
    debug="${2:-$SALT_BOOT_DEBUG}"
    bs_yellow_log "----------------------------------------------------------"
    bs_yellow_log " MAKINA-STATES BOOTSTRAPPER (@$(get_ms_branch)) FOR $SALT_BOOT_OS"
    bs_yellow_log "   - ${THIS} [--help] [--long-help]"
    bs_yellow_log " Those informations have been written to:"
    bs_yellow_log "   - ${TMPDIR}/boot_salt_top"
    bs_yellow_log "----------------------------------------------------------"
    bs_yellow_log "HOST variables:"
    bs_yellow_log "---------------"
    if [ "x$(get_local_mastersalt_mode)" = "xremote" ];then
	    bs_log "NICKNAME_FQDN/HOST/DOMAIN: ${NICKNAME_FQDN}/${HOST}/${DOMAINNAME}"
    else
	    bs_log "Light install, minion id: $(get_minion_id)"
    fi
    bs_log "DATE: ${CHRONO}"
    bs_log "LOCAL_SALT_MODE: $(get_local_salt_mode)"
    bs_log "LOCAL_MASTERSALT_MODE: $(get_local_mastersalt_mode)"
    bs_log "SALT_NODETYPE: $(get_salt_nodetype)"
    if [ "x${SALT_REATTACH}" != "x" ];then
        bs_log "-> SaltCloud mode"
    fi
    if [ "x${MAKINASTATES_TEST}" != "x" ];then
        bs_log "-> Will run tests"
    fi
    if [ "x${IS_SALT_UPGRADING}" != "x" ];then
        bs_log "-> Will upgrade makina-states"
    fi
    if [ "x${debug}" != "x" ];then
        bs_log "ROOT: $ROOT"
        bs_log "PREFIX: $PREFIX"
    fi
    if [ "x${VENV_REBOOTSTRAP}" != "x" ];then
        bs_log "Rebootstrap virtualenv"
    fi
    if [ "x${SALT_REBOOTSTRAP}" != "x" ];then
        bs_log "Rebootstrap salt"
    fi
    if [ "x${IS_SALT}" != "x" ];then
        bs_yellow_log "---------------"
        bs_yellow_log "SALT variables:"
        bs_yellow_log "---------------"
        bs_log "SALT ROOT | PILLAR: ${SALT_ROOT} | ${SALT_PILLAR}"
        if [ "x${IS_SALT_MASTER}" != "x" ];then
            bs_log "SALT_MASTER_IP: ${SALT_MASTER_IP}"
        fi
        if [ "x${IS_SALT_MINION}" != "x" ];then
            bs_log "SALT_MASTER_DNS: $SALT_MASTER_DNS"
            bs_log "SALT_MASTER_PORT: ${SALT_MASTER_PORT}"
            bs_log "SALT_MINION_IP: $SALT_MINION_IP"
            bs_log "SALT_MINION_ID: $SALT_MINION_ID"
        fi
        if [ "x${debug}" != "x" ];then
            bs_log "SALT_MASTER_PUBLISH_PORT: $SALT_MASTER_PUBLISH_PORT"
            bs_log "salt_bootstrap_nodetype: $salt_bootstrap_nodetype"
            if [ "x${IS_SALT_MASTER}" != "x" ];then
                bs_log "salt_bootstrap_master: $salt_bootstrap_master"
                bs_log "SALT_MASTER_CONTROLLER: $SALT_MASTER_CONTROLLER"
                debug_msg "SALT_MASTER_CONTROLLER_INPUTED: $SALT_MASTER_CONTROLLER_INPUTED"
            fi
            if [ "x${IS_SALT_MINION}" != "x" ];then
                bs_log "salt_bootstrap_minion: $salt_bootstrap_minion"
                bs_log "SALT_MINION_CONTROLLER: $SALT_MINION_CONTROLLER"
                debug_msg "SALT_MINION_CONTROLLER_INPUTED: $SALT_MINION_CONTROLLER_INPUTED"
            fi
        fi
    fi
    if [ "x${IS_MASTERSALT}" != "x" ];then
        bs_yellow_log "---------------------"
        bs_yellow_log "MASTERSALT variables:"
        bs_yellow_log "---------------------"
        bs_log "MASTERSALT ROOT | PILLAR: ${MASTERSALT_ROOT} | ${MASTERSALT_PILLAR}"
        bs_log "MASTERSALT: ${MASTERSALT}"
        if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            bs_log "MASTERSALT_MASTER_IP: ${MASTERSALT_MASTER_IP}"
            bs_log "MASTERSALT_MASTER_PUBLISH_PORT ${MASTERSALT_MASTER_PUBLISH_PORT}"
        fi
        if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
            bs_log "MASTERSALT_MASTER_PORT: ${MASTERSALT_MASTER_PORT}"
            bs_log "MASTERSALT_MINION_IP: ${MASTERSALT_MINION_IP}"
            debug_msg "MASTERSALT_INPUTED: ${MASTERSALT_INPUTED}"
            if [ "x${MASTERSALT_MINION_ID}" != "x${SALT_MINION_ID}" ];then
                bs_log "MASTERSALT_MINION_ID: ${MASTERSALT_MINION_ID}"
            fi
        fi
        if [ "x${debug}" != "x" ];then
            bs_log "mastersalt_bootstrap_nodetype: ${mastersalt_bootstrap_nodetype}"
            if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
                bs_log "mastersalt_bootstrap_master: ${mastersalt_bootstrap_master}"
                bs_log "MASTERSALT_MASTER_CONTROLLER: ${MASTERSALT_MASTER_CONTROLLER}"
                debug_msg "MASTERSALT_MASTER_CONTROLLER_INPUTED: ${MASTERSALT_MASTER_CONTROLLER_INPUTED}"
            fi
            if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
                bs_log "mastersalt_bootstrap_minion: ${mastersalt_bootstrap_minion}"
                bs_log "MASTERSALT_MINION_CONTROLLER: ${MASTERSALT_MINION_CONTROLLER}"
                debug_msg "MASTERSALT_MINION_CONTROLLER_INPUTED: ${MASTERSALT_MINION_CONTROLLER_INPUTED}"
            fi
        fi
    fi
    if [ "x${IS_SALT}" != "x" ];then
        for i in \
            "${SALT_MASTER_IP}" "$SALT_MINION_IP";\
        do
            thistest="$(echo "${i}"|grep -q "${DNS_RESOLUTION_FAILED}")"
            if [ "x${thistest}" = "x0" ];then
                die "$DNS_RESOLUTION_FAILED"
            fi
        done
    fi
    if [ "x${IS_MASTERSALT}" != "x" ];then
        for i in  "${MASTERSALT_MINION_IP}";\
        do
            thistest="$(echo "${i}"|grep -q "${DNS_RESOLUTION_FAILED}")"
            if [ "x${thistest}" = "x0" ];then
                die "${DNS_RESOLUTION_FAILED}"
            fi
        done
    fi
    bs_yellow_log "---------------------------------------------------"
    if [ "x${need_confirm}" != "xno" ] && [ "x${SALT_BOOT_NOCONFIRM}" = "x" ];then
        bs_yellow_log "To not have this confirmation message, do:"
        bs_yellow_log "    export SALT_BOOT_NOCONFIRM='1'"
        interactive_tempo 60
    fi
}

recap() {
    will_do_recap="x"
    if [ "x${SALT_BOOT_CHECK_ALIVE}" != "x" ];then
        will_do_recap=""
    fi
    if [ "x${QUIET}" != "x" ];then
        will_do_recap=""
    fi
    if [ "x${will_do_recap}" != "x" ];then
        recap_
        travis_sys_info
    fi
    recap_ "no" "y" > "${TMPDIR}/boot_salt_top"
}

is_apt_installed() {
    if [ "x$(dpkg-query -s ${@} 2>/dev/null|egrep "^Status:"|grep installed|wc -l|${SED} -e "s/ //g")"  = "x0" ];then
        echo "no"
    else
        echo "yes"
    fi
}

lazy_apt_get_install() {
    to_install=""
    for i in ${@};do
         if [ "x$(is_apt_installed ${i})" != "xyes" ];then
             to_install="$to_install ${i}"
         fi
    done
    if [ "x${to_install}" != "x" ];then
        bs_log "Installing $to_install"
        apt-get install -y --force-yes $to_install
    fi
}

setup_backports() {
    # on ubuntu enable backports release repos, & on debian just backport
    if [ "x${BEFORE_SAUCY}" != "x" ] && [ "x${IS_UBUNTU}" != "x" ];then
        bs_log "Activating backport from ${DISTRIB_BACKPORT} to ${DISTRIB_CODENAME}"
        cp  ${CONF_ROOT}/apt/sources.list "${CONF_ROOT}/apt/sources.list.${CHRONO}.sav"
        "${SED}" -i -e "s/${DISTRIB_CODENAME}/${DISTRIB_BACKPORT}/g" "${CONF_ROOT}/apt/sources.list"
    fi
    if [ "x${IS_DEBIAN}" != "x" ];then
        bs_log "Activating backport from ${DISTRIB_BACKPORT} to ${DISTRIB_CODENAME}"
        cp  ${CONF_ROOT}/apt/sources.list "${CONF_ROOT}/apt/sources.list.${CHRONO}.sav"
        "${SED}" "/^deb.*${DISTRIB_BACKPORT}/d" -i ${CONF_ROOT}/apt/sources.list
        echo "#backport added by boot-salt">/tmp/aptsrc
        egrep "^deb.* ${DISTRIB_CODENAME} " ${CONF_ROOT}/apt/sources.list|"${SED}" -i -e "s/${DISTRIB_CODENAME}/${DISTRIB_BACKPORT}/g" > /tmp/aptsrc
        cat /tmp/aptsrc >> ${CONF_ROOT}/apt/sources.list
        rm -f /tmp/aptsrc
    fi

}

teardown_backports() {
    # on ubuntu disable backports release repos, & on debian just backport

    if [ "x${BEFORE_SAUCY}" != "x" ] && [ "x${IS_UBUNTU}" != "x" ];then
        bs_log "Removing backport from $DISTRIB_BACKPORT to $DISTRIB_CODENAME"
        "${SED}" -i -e "s/${DISTRIB_BACKPORT}/${DISTRIB_CODENAME}/g" "${CONF_ROOT}/apt/sources.list"
    fi
    # leave the backport in placs on debian
}

install_prerequisites() {
    to_install=""
    if [ "x${QUIET}" = "x" ];then
        bs_log "Check package dependencies"
    fi
    lazy_apt_get_install python-software-properties
    # XXX: only lts package in this ppa
    if [ "x${DISTRIB_CODENAME}" != "xlenny" ];then
        if     [ "x$(is_apt_installed libzmq3    )" = "xno" ] \
            || [ "x$(is_apt_installed libzmq3-dev)" = "xno" ];\
            then
            bs_log "Installing ZeroMQ3"
            setup_backports
            apt-get remove -y --force-yes libzmq libzmq1 libzmq-dev 1>/dev/null 2>/dev/null
            apt-get update -qq && lazy_apt_get_install libzmq3-dev
            ret="${?}"
            if [ "x${ret}" != "x0" ];then
                die_ ${ret} "Install of zmq3 failed"
            fi
            ret="${?}"
            teardown_backports && apt-get update
            if [ "x${ret}" != "x0" ];then
                die_ ${ret} "Teardown backports failed"
            fi
        fi
    fi
    for i in ${BASE_PACKAGES};do
        if [ "x$(dpkg-query -s ${i} 2>/dev/null|egrep "^Status:"|grep installed|wc -l|${SED} -e "s/ //g")" = "x0" ];then
            to_install="${to_install} ${i}"
        fi
    done
    if [ "x${to_install}" != "x" ];then
        bs_log "Installing pre requisites: ${to_install}"
        echo 'changed=yes comment="prerequisites installed"'
        apt-get update && lazy_apt_get_install ${to_install}
    fi
}

# check if salt got errors:
# - First, check for fatal errors (retcode not in [0, 2]
# - in case of executions:
# - We will check for fatal errors in logs
# - We will check for any false return in output state structure
get_saltcall_args() {
    LOCAL=""
    if [ "x$(get_local_salt_mode)" = "xmasterless" ];then
        LOCAL="--local"
    fi
    echo "${LOCAL} $(get_module_args "${LOCAL}" "${SALT_ROOT}" "${SALT_MS}")"
}

get_mastersaltcall_args() {
    get_module_args "${MASTERSALT_ROOT}" "${MASTERSALT_MS}"
}

salt_call_wrapper_() {
    last_salt_retcode=-1
    salt_call_prefix=${1};shift
    outf="${SALT_BOOT_OUTFILE}"
    logf="${SALT_BOOT_LOGFILE}"
    cmdf="${SALT_BOOT_CMDFILE}"
    saltargs=" --retcode-passthrough --out=yaml --out-file="$outf" --log-file="$logf""
    if [ "x${SALT_BOOT_DEBUG}" != "x" ];then
        saltargs="${saltargs} -l${SALT_BOOT_DEBUG_LEVEL}"
    else
        saltargs="${saltargs} -lquiet"
    fi
    if [ "x${SALT_NODETYPE}" = "xtravis" ];then
        touch /tmp/travisrun
        ( while [ -f /tmp/travisrun ];do sleep 15;echo "keep me open";sleep 45;done; )&
    fi
    echo "$(date): ${salt_call_prefix}/bin/salt-call $saltargs ${@}" >> "$cmdf"
    ${salt_call_prefix}/bin/salt-call ${saltargs} ${@}
    last_salt_retcode=${?}
    if [ "x${SALT_NODETYPE}" = "xtravis" ];then
        rm -f /tmp/travisrun
    fi
    STATUS="NOTSET"
    yaml_check=1
    if [ -e "${outf}" ];then
      stmpf=$(mktemp)
      cat > "${stmpf}" << EOF
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
import yaml, sys, codecs
from pprint import pprint
ret = 0
statecheck = False
for i in ['state.highstate', 'state.sls']:
    if i in "${saltargs//\"/} ${@//\"/}":
        statecheck = True
if statecheck:
    with codecs.open("$outf", "r", "utf-8") as fic:
        fdata = fic.read()
        if not fdata:
            print("no file content")
            sys.exit(1)
        data = yaml.load(fdata)
        if not isinstance(data, dict):
            print("no state data in\n{0}".format(pprint(data)))
            sys.exit(1)
        for i, rdata in data.items():
            if not isinstance(rdata, dict):
                print("no state rdata in\n{0}".format(pprint(rdata)))
                sys.exit(1)
            if ret:
                break
            for j, statedata in rdata.items():
                if statedata.get('result', None) is False:
                    pprint(statedata)
                    ret = 1
                    break
sys.exit(ret)
EOF
        "${salt_call_prefix}/bin/python" "${stmpf}"
        yaml_check=${?}
        rm -f "${stmpf}"
    fi
    if [ "x${yaml_check}" != "x0" ] && [ "x${last_salt_retcode}" != "x0" ] && [ "x${last_salt_retcode}" != "x2" ];then
        STATUS="ERROR"
        bs_log "salt-call ERROR, check ${logf} and ${outf} for details" 2>&2
        last_salt_retcode=100
    fi
    no_output_log=""
    if [ -e "$logf" ];then
        if grep  -q "No matching sls found" "$logf";then
            STATUS="ERROR"
            bs_log "salt-call  ERROR DETECTED : No matching sls found" 1>&2
            last_salt_retcode=101
            no_output_log="y"
        elif egrep -q "\[salt.(state|crypt)[ ]*\]\[(ERROR|CRITICAL)[ ]*\]" "$logf";then
            STATUS="ERROR"
            bs_log "salt-call  ERROR DETECTED, check ${logf} for details" 1>&2
            egrep "\[salt.state       \]\[ERROR   \]" "${logf}" 1>&2;
            last_salt_retcode=102
            no_output_log="y"
        elif egrep  -q "Rendering SLS .*failed" "${logf}";then
            STATUS="ERROR"
            bs_log "salt-call  ERROR DETECTED : Rendering failed" 1>&2
            last_salt_retcode=103
            no_output_log="y"
        fi
    fi
    if [ -e "${outf}" ];then
        if [ "x${yaml_check}" = "x0" ];then
            last_salt_retcode=0
            STATUS="OK"
        elif [ "x${yaml_check}" != "x0" ];then
            if [ "x${no_output_log}" = "x" ];then
                bs_log "partial content of $outf, check this file for full output" 1>&2
            fi
            egrep -B4 "result: false" "${outf}" 1>&2;
            last_salt_retcode=104
            STATUS="ERROR"
        elif egrep  -q "Rendering SLS .*failed" "${outf}";then
            if [ "x${no_output_log}" = "x" ];then
                bs_log "salt-call  ERROR DETECTED : Rendering failed (o)" 1>&2
            fi
            last_salt_retcode=103
            STATUS="ERROR"
        fi
    fi
    if [ "x${STATUS}" != "xERROR" ] \
        && [ "x${last_salt_retcode}" != "x0" ]\
        && [ "x${last_salt_retcode}" != "x2" ];\
    then
        last_salt_retcode=0
    fi
    for i in "${SALT_BOOT_OUTFILE}" "${SALT_BOOT_LOGFILE}" "${SALT_BOOT_CMDFILE}";do
        if [ -e "${i}" ];then
            chmod 600 "${i}" 1>/dev/null 2>/dev/null
        fi
    done
}

salt_call_wrapper() {
    chrono="$(get_full_chrono)"
    if [ ! -d "${BOOT_LOGS}" ];then
        mkdir -pv "${BOOT_LOGS}"
    fi
    SALT_BOOT_OUTFILE="${BOOT_LOGS}/boot_salt.${chrono}.out"
    SALT_BOOT_LOGFILE="${BOOT_LOGS}/boot_salt.${chrono}.log"
    SALT_BOOT_CMDFILE="${BOOT_LOGS}/boot_salt_cmd"
    salt_call_wrapper_ "${SALT_MS}" $(get_saltcall_args) ${@}
}

mastersalt_call_wrapper() {
    chrono="$(get_full_chrono)"
    if [ ! -d "${MBOOT_LOGS}" ];then
        mkdir -pv ${MBOOT_LOGS}
    fi
    SALT_BOOT_OUTFILE="${MBOOT_LOGS}/boot_salt.${chrono}.out"
    SALT_BOOT_LOGFILE="${MBOOT_LOGS}/boot_salt.${chrono}.log"
    SALT_BOOT_CMDFILE="${MBOOT_LOGS}/boot_salt_cmd"
    salt_call_wrapper_ "${MASTERSALT_MS}" $(get_mastersaltcall_args) -c ${MCONF_PREFIX} ${@}
}

get_grain() {
    salt-call --local grains.get ${1} --out=raw 2>/dev/null
}

set_grain() {
    grain="${1}"
    bs_log "Testing salt grain '${grain}'"
    if [ "x$(get_grain ${grain}|grep -iq True;echo $?)" != "x0" ];then
        bs_log "Setting salt grain: ${grain}=true "
        salt-call --local grains.setval ${grain} true
        # sync grains rigth now, do not wait for reboot
        die_in_error "setting ${grain}"
        salt-call --local saltutil.sync_grains 1>/dev/null 2>/dev/null
    else
        bs_log "Grain '${grain}' already set"
    fi
}

check_restartmarker_and_maybe_restart() {
    if [ "x${SALT_BOOT_IN_RESTART}" = "x" ] && [ "x${SALT_REATTACH}" = "x" ];then
        if [ "x${SALT_BOOT_NEEDS_RESTART}" != "x" ];then
            touch "${SALT_MS}/.bootsalt_need_restart"
        fi
        if [ -e "${SALT_MS}/.bootsalt_need_restart" ] && [ "x${SALT_BOOT_NO_RESTART}" = "x" ];then
            chmod +x "${SALT_MS}/_scripts/boot-salt.sh"
            export SALT_BOOT_NO_RESTART="1"
            export SALT_BOOT_IN_RESTART="1"
            export SALT_BOOT_NOCONFIRM='1'
            mbootsalt="${MASTERSALT_MS}/_scripts/boot-salt.sh"
            bootsalt="${SALT_MS}/_scripts/boot-salt.sh"
            if [ "x${THIS}" = "x${mbootsalt}" ];then
                bootsalt="${mbootsalt}"
            fi
            if [ "x${QUIET}" = "x" ];then
                bs_log "Restarting ${bootsalt} which needs to update itself"
            fi
            "${bootsalt}" ${LAUNCH_ARGS} && rm -f "${SALT_MS}/.bootsalt_need_restart"
            exit ${?}
        fi
    fi
}

sys_info(){
    set -x
    ps aux
    ps aux|grep salt
    netstat -pnlt
    for i in salt-master salt-minion;do
        if [ -e "/var/log/salt/${i}" ];then
            cat "/var/log/salt/${i}"
        fi
    done
    set +x
}

travis_sys_info() {
    if [ "x${SALT_NODETYPE}" = "xtravis" ] && [ "x${TRAVIS_DEBUG}" != "x" ];then
        sys_info
    fi
}

get_git_branch() {
    cd "${1}" 1>/dev/null 2>/dev/null
    br="$(git branch | grep "*"|grep -v grep)"
    echo "${br}"|"${SED}" -e "s/\* //g"
    cd - 1>/dev/null 2>/dev/null
}

get_salt_mss() {
    SALT_MSS=""
    if [ "x${IS_SALT}" != "x" ];then
        SALT_MSS="${SALT_MSS} ${SALT_MS}"
    fi
    if [ "x${IS_MASTERSALT}" != "x" ];then
        SALT_MSS="${SALT_MSS} ${MASTERSALT_MS}"
    fi
    echo ${SALT_MSS}
}

is_basedirs_there() {
    there="1"
    for dir in $(get_salt_mss);do
        for subdir in "${dir}" "${dir}/src/salt";do
            if [ ! -e "${dir}" ];then
                there=""
            fi
        done
    done
    echo "${there}"
}

setup_and_maybe_update_code() {
    onlysync=""
    for arg in ${@};do
        if [ "x${arg}" = "xonlysync" ];then
            onlysync="y"
        fi
    done
    if [ "x${QUIET}" = "x" ];then
        bs_log "Create base directories"
    fi
    if [ "x${IS_SALT}" != "x" ];then
        for i in "${SALT_PILLAR}" "${SALT_ROOT}";do
            if [ ! -d "${i}" ];then
                mkdir -pv "${i}"
            fi
        done
    fi
    if [ "x${IS_MASTERSALT}" != "x" ];then
        for i in "${MASTERSALT_PILLAR}" "${MASTERSALT_ROOT}";do
            if [ ! -d "${i}" ];then
                mkdir -pv "${i}"
            fi
        done
    fi
    SALT_MSS="$(get_salt_mss)"
    is_offline="$(test_online)"
    minion_keys="$(find "${CONF_PREFIX}/pki/master/"{minions_pre,minions} -type f 2>/dev/null|wc -l|${SED} -e "s/ //g")"
    if [ "x${is_offline}" != "x0" ];then
        if [ ! -e "${CONF_PREFIX}" ]\
            || [ "x${minion_keys}" = "x0" ]\
            || [ ! -e "${SALT_MS}/src/salt" ]\
            || [ ! -e "${SALT_MS}/bin/salt-call" ]\
            || [ ! -e "${SALT_MS}/bin/salt" ];then
            bs_log "Offline mode and installation not enougthly completed, bailing out"
            exit 1
        fi
    fi
    if [ "x${SALT_BOOT_IN_RESTART}" = "x" ] && [ "x${is_offline}" = "x0" ];then
        install_prerequisites || die " [bs] Failed install rerequisites"
        skip_co="${SALT_BOOT_SKIP_CHECKOUTS}"
        if [ "x$(is_basedirs_there)" = "x" ];then
            skip_co=""
        fi
        if [ "x${skip_co}" = "x" ];then
            if [ "x${QUIET}" = "x" ];then
                bs_yellow_log "If you want to skip checkouts, next time do export SALT_BOOT_SKIP_CHECKOUTS=1"
            fi
            for ms in ${SALT_MSS};do
                if [ ! -d "${ms}/.git" ];then
                        remote="remotes/origin/"
                        branch_pref=""
                        ms_branch="$(get_ms_branch)"
                        thistest="$(echo "${ms_branch}" | grep -q "changeset:";echo "${?}")"
                        if [ "x${thistest}" = "x0" ];then
                            ms_branch="$(echo "${ms_branch}"|${SED} -e "s/changeset://g")"
                            remote=""
                            branch_pref="changeset_"
                        fi
                        git clone ${QUIET_GIT} "${MAKINASTATES_URL}" "${ms}" &&\
                        cd "${ms}" &&\
                        git checkout ${QUIET_GIT} "${remote}""${ms_branch}" -b "${branch_pref}""${ms_branch}" &&\
                        cd - 1>/dev/null 2>/dev/null
                    SALT_BOOT_NEEDS_RESTART="1"
                    if [ "x${?}" = "x0" ];then
                        if [ "x${QUIET}" = "x" ];then
                            bs_yellow_log "Downloaded makina-states (${ms})"
                        fi
                    else
                        die " [bs] Failed to download makina-states (${ms})"
                    fi
                fi
                #chmod +x ${SALT_MS}/_scripts/install_salt_modules.sh
                #"${SALT_MS}/_s
                cd "${ms}"
                if [ ! -e src ];then
                    link_salt_dir "${ms}"
                fi
                if [ ! -e src ];then
                    echo "pb with linking venv in ${ms}"
                    exit 1
                fi
                for i in "${ms}" "${ms}/src/"*;do
                    is_changeset=""
                    branch_pref=""
                    do_update="y"
                    if [ "x${onlysync}" != "x" ];then
                        if [ "x$(echo "${i}"|${SED} -e "s/.*\(\(salt\)\|\(makina-states\)\)$/match/g")" != "xmatch" ];then
                            do_update=""
                            if [ "x${QUIET}" = "x" ];then
                                bs_log "Skipping ${i} update as it is only a base salt sync"
                            fi
                        fi
                    fi
                    if [ -e "${i}/.git" ] && [ "x${do_update}" != "x" ];then
                        "${SED}" -i -e "s/filemode =.*/filemode=false/g" "${i}/.git/config" 2>/dev/null
                        remote="remotes/origin/"
                        co_branch="master"
                        pref=""
                        if [ "x${i}" = "x${ms}" ];then
                            co_branch="$(get_ms_branch "${i}")"
                            thistest="$(echo "${co_branch}" | grep -q "changeset:";echo "${?}")"
                            if [ "x${thistest}" = "x0" ];then
                                co_branch="$(echo "${co_branch}"|${SED} -e "s/changeset://g")"
                                pref="changeset:"
                                is_changeset="1"
                                branch_pref="changeset_"
                                remote=""
                            fi
                        fi
                        if  [ "x${i}" = "x${ms}/src/salttesting" ]\
                         || [ "x${i}" = "x${ms}/src/SaltTesting" ]\
                         || [ "x${i}" = "x${ms}/src/salt" ];then
                            co_branch="develop"
                        fi
                        if [ "x${QUIET}" = "x" ];then
                            bs_log "Upgrading ${i}"
                        fi
                        cd "${i}"
                        git fetch --tags origin 1>/dev/null 2>/dev/null
                        git fetch ${QUIET_GIT} origin
                        lbranch="$(get_git_branch .)"
                        if [ "x${lbranch}" != "x${branch_pref}${co_branch}" ];then
                            if [ "x$(git branch|egrep " ${co_branch}\$" |wc -l|${SED} -e "s/ //g")" != "x0" ];then
                                # branch already exists
                                if [ "x${QUIET}" = "x" ];then
                                    bs_log "Switch branch: ${lbranch} -> ${branch_pref}${co_branch}"
                                fi
                                git checkout ${QUIET_GIT} "${branch_pref}""${co_branch}"
                                ret="${?}"
                            else
                                # branch  does not exist yet
                                if [ "x${QUIET}" = "x" ];then
                                    bs_log "Create & switch on branch: ${branch_pref}${co_branch} from ${lbranch}"
                                fi
                                git checkout ${QUIET_GIT} "${remote}""${co_branch}" -b "${branch_pref}""${co_branch}"
                                ret="${?}"
                            fi
                            if [ "x${ret}" != "x0" ];then
                                die "Failed to switch branch: ${lbranch} -> ${branch_pref}${co_branch}"
                            else
                                if [ "x${QUIET}" = "x" ];then
                                    bs_log "Update is necessary"
                                fi
                                SALT_BOOT_NEEDS_RESTART="1"
                            fi
                        else
                            if [ "x${is_changeset}" != "x1" ];then
                                git diff ${QUIET_GIT} origin/${co_branch} --exit-code 1>/dev/null 2>/dev/null
                                if [ "x${?}" != "x0" ];then
                                    if [ "x${QUIET}" = "x" ];then
                                        bs_log "Update is necessary"
                                    fi
                                fi && if \
                                    [ "x${i}" = "x${ms}/src/SaltTesting" ] || [ "x${i}" = "x${ms}/src/salttesting" ]\
                                ;then
                                    git reset ${QUIET_GIT} --hard origin/${co_branch}
                                else
                                    git merge ${QUIET_GIT} --ff-only origin/${co_branch}
                                fi
                                SALT_BOOT_NEEDS_RESTART=1
                            fi
                        fi
                        if [ "x${?}" = "x0" ];then
                            if [ "x${QUIET}" = "x" ];then
                                bs_yellow_log "Downloaded/updated ${i}"
                            fi
                        else
                            die "Failed to download/update ${i}"
                        fi
                        if [ "x${i}" = "x${ms}" ];then
                            store_conf branch "${pref}${co_branch}"
                        fi
                    fi
                done
            done
        fi
    fi
    check_restartmarker_and_maybe_restart
    if [ "x${SALT_BOOT_IN_RESTART}" = "x" ] && [ "x$(is_basedirs_there)" = "x" ];then
        die "Base directories are not present"
    fi
}

service_() {
    s="${1}"
    shift
    if [ "x$(grep -q manual /etc/init/${s}.override 2>/dev/null)" != "x0" ];then
        if [ -e "$(which service 2>/dev/null)" ];then
            service "${s}" "${@}"
        else
            /etc/init.d/${s} "${@}"
        fi
    fi
}

cleanup_previous_venv() {
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
    if [ -e "${1}" ];then
        old_d="${PWD}"
        cd "${1}"
        CWD="${PWD}"
        for i in "${ROOT}" "${ROOT}usr" "${ROOT}usr/local";do
            if [ "x${CWD}" = "x${i}" ];then
                die "[bs] wrong dir for venv: '${i}'"
            fi
        done
        for item in ${VENV_CONTENT};do
            for i in $(find ${item} -maxdepth 0 2>/dev/null);do
                bs_log "Cleaning ${i}"
                rm -rfv "${i}"
                VENV_REBOOTSTRAP="y"
            done
        done
        cd "${old_d}"
    fi
}

setup_virtualenvs() {
    setup_virtualenv "${SALT_VENV_PATH}"
    if [ "x${IS_MASTERSALT}" != "x" ];then
        setup_virtualenv "${MASTERSALT_VENV_PATH}"
    fi
}

setup_virtualenv() {
    # Script is now running in makina-states git location
    # Check for virtualenv presence
    venv_path="${1:-${SALT_VENV_PATH}}"
    ms_path="$(get_makina_states ${venv_path})"
    REBOOTSTRAP="${VENV_REBOOTSTRAP:-${SALT_REBOOTSTRAP}}"
    # cleanup_previous_venv "/srv/salt-venv"
    if [ ! -e "${ms_path}" ];then
        echo missing makina-states in ${ms_path}
        exit 1
    fi
    cd "${ms_path}"
    if     [ ! -e "${venv_path}/bin/activate" ] \
        || [ ! -e "${venv_path}/lib" ] \
        || [ ! -e "${venv_path}/include" ] \
        ;then
        bs_log "Creating virtualenv in ${venv_path}"
        vargs=""
        if [ "x${DISTRIB_CODENAME}" = "xlenny" ];then
            vargs="--python=$(which python2.7)"
        fi
        if [ ! -e "${PIP_CACHE}" ];then
            mkdir -p "${PIP_CACHE}"
        fi
        if [ ! -e "${venv_path}" ];then
            mkdir -p "${venv_path}"
        fi
        virtualenv $vargs --system-site-packages --unzip-setuptools ${venv_path} &&\
        . "${venv_path}/bin/activate" &&\
        "${venv_path}/bin/easy_install" -U setuptools &&\
        "${venv_path}/bin/pip" install -U pip&&\
        deactivate
        BUILDOUT_REBOOTSTRAP=y
        SALT_REBOOTSTRAP=y
    fi

    # virtualenv is present, activate it
    if [ -e "${venv_path}/bin/activate" ];then
        if [ "x${QUIET}" = "x" ];then
            bs_log "Activating virtualenv in ${venv_path}"
        fi
        . "${venv_path}/bin/activate"
    fi
    # install requirements
    cd "${ms_path}"
    install_git=""
    for i in ${EGGS_GIT_DIRS};do
        if [ ! -e "${venv_path}/src/${i}" ];then
            install_git="x"
        fi
    done
    uflag=""
    # only install git reqs in upgade mode if not already there
    if [ ! -e requirements/requirements.txt ];then
        git pull
    fi
    pip install -U --download-cache "${PIP_CACHE}" -r requirements/requirements.txt
    if [ "x${install_git}" != "x" ];then
        pip install -U --download-cache "${PIP_CACHE}" -r requirements/git_requirements.txt
    fi
    pip install --no-deps -e .
    link_salt_dir "${ms_path}" "${venv_path}"
}


get_makina_states() {
    if [ "x${1}" = "x${MASTERSALT_VENV_PATH}" ];then
        venv_dir="${MASTERSALT_MS}"
    else
        venv_dir="${SALT_MS}"
    fi
    echo "${venv_dir}"
}

get_venv_path() {
    if [ "x${1}" = "x${MASTERSALT_MS}" ];then
        makina_states_dir="${MASTERSALT_VENV_PATH}"
    else
        makina_states_dir="${SALT_VENV_PATH}"
    fi
    echo "${makina_states_dir}"
}

link_salt_dir() {
    where="${1}"
    vpath="${2:-$(get_venv_path "${where}")}"
    checkreq=""
    for i in ${EGGS_GIT_DIRS};do
        i="${venv_path}/src/${i}"
        if [ ! -e "${i}" ];then
            echo "   * ${i} is not present"
            checkreq="1"
        fi
    done
    for i in \
        bin/salt-call\
        bin/salt\
        bin/pip\
        bin/easy_install\
        bin/activate\
        bin/salt-master\
        bin/python;do
        if [ ! -e "${venv_path}/${i}" ];then
            echo "   * ${i} is not present"
            checkreq="1"
        fi
    done
    if [ "x${checkreq}" != "x" ];then
        echo "prerequisites not achieved, there is a problem with pip install !"
        exit 1
    fi
    for i in share man lib include bin src;do
        if [ -d "${where}/${i}" ] && [ ! -h "${where}/${i}" ];then
            if [ ! -e "${where}/nobackup" ];then
                mkdir "${where}/nobackup"
            fi
            echo "moving old directory; \"${where}/${i}\" to \"${where}/nobackup/${i}-$(date "+%F-%T-%N")\""
            mv "${where}/${i}" "${where}/nobackup/${i}-$(date "+%F-%T-%N")"
        fi
        do_link="1"
        if [ -h "${where}/${i}" ];then
            if [ "x$(readlink ${where}/${i})" != "${vpath}/${i}" ];then
                do_link=""
            fi
        fi
        if [ "x${do_link}" != "x" ];then
            ln -sfv "${vpath}/${i}" "${where}/${i}"
        fi
    done
}

__install() {
    origin="${1}"
    dest="${2}"
    if [ -e "${origin}" ];then
        container="$(dirname ${dest})"
        if [ -e "${container}" ];then
            mkdir -pv "${container}"
        fi
        cp -rvf "${origin}" "${dest}"
    fi
}

kill_ms_daemons() {
    upgrade_from_buildout
    killall_local_mastersalt_masters
    killall_local_mastersalt_minions
    killall_local_minions
    killall_local_masters
}

regenerate_openssh_keys() {
    bs_log "Regenerating sshd server keys"
    /bin/rm /etc/ssh/ssh_host_*
    dpkg-reconfigure openssh-server
}

get_yaml_value() {
    gyaml_file="${1}"
    gyaml_param="${2}"
    egrep "^${gyaml_param}: " "${gyaml_file}" 2>/dev/null|tail -n1|${SED} -re "s/^(${gyaml_param}): (.*)$/\2/g"
}

edit_yaml_file() {
    yaml_old_value=""
    yaml_file_changed="0"
    yaml_file="${1}"
    shift
    yaml_param="${1}"
    shift
    yaml_value=$@
    yaml_edit_value="0"
    yaml_edited_value="0"
    yaml_added_value="0"
    yaml_add_value="0"
    if [ -e "${yaml_file}" ] && [ ! -d "${yaml_file}" ];then
        if [ "x$(egrep -q "^${yaml_param}: " "${yaml_file}" 2>/dev/null;echo ${?})" = "x0" ];then
            yaml_edit_value="1"
        fi
        if [ "x${yaml_edit_value}" != "x0" ];then
            yaml_old_value=$(get_yaml_value "${yaml_file}" "${yaml_param}")
            if [ "x${yaml_old_value}" != "x${yaml_value}" ];then
                yaml_file_changed="1"
                yaml_edited_value="1"
                yaml_add_value="1"
                ${SED} -i -re "/^${yaml_param}: /d" "${yaml_file}"
            fi
        else
            yaml_add_value="1"
            yaml_added_value="1"
        fi
        if [ "x${yaml_add_value}" != "x0" ];then
            yaml_file_changed="1"
            echo >> "${yaml_file}"
            echo "${yaml_param}: ${yaml_value}" >> "${yaml_file}"
            echo >> "${yaml_file}"
        fi
    fi
}

reconfigure_mastersalt_master() {
    branch_id="$(get_ms_branch|"${SED}" -e "s/changeset://g")"
    master="${1:-${MASTERSALT_MASTER_DNS}}"
    master_ip="${2:-${MASTERSALT_MASTER_IP}}"
    port="${3:-${MASTERSALT_MASTER_PORT}}"
    publish_port="${4:-${MASTERSALT_MASTER_PUBLISH_PORT}}"
    mastersalt_master_changed="${mastersalt_master_changed:-"0"}"
    if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
        for conf in "${MASTERSALT_PILLAR}/mastersalt_minion.sls" "${MASTERSALT_PILLAR}/mastersalt.sls";do
            edit_yaml_file "${conf}" makina-states.controllers.salt_master.settings.interface "${master_ip}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_master_changed="1"
            fi
            edit_yaml_file "${conf}" makina-states.controllers.salt_master.settings.publish_port "${publish_port}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_master_changed="1"
            fi
            edit_yaml_file "${conf}" makina-states.controllers.salt_master.settings.ret_port "${port}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_master_changed="1"
            fi
        done
        for conf in "${MCONF_PREFIX}"/master "${MCONF_PREFIX}"/master.d/*;do
            if [ -f "${conf}" ];then
                edit_yaml_file "${conf}" interface "${SALT_MASTER_IP}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    mastersalt_master_changed="1"
                fi
                edit_yaml_file "${conf}" ret_port "${SALT_MASTER_PORT}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    mastersalt_master_changed="1"
                fi
                edit_yaml_file "${conf}" publish_port "${SALT_MASTER_PUBLISH_PORT}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    mastersalt_master_changed="1"
                fi
                edit_yaml_file "${conf}" "${BRANCH_PILLAR_ID}" "${branch_id}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    mastersalt_master_changed="1"
                fi
            fi
        done
        edit_yaml_file "${MCONF_PREFIX}/grains" makina-states.controllers.mastersalt_master true
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_master_changed="1"
        fi
    else
        edit_yaml_file "${MCONF_PREFIX}/grains" makina-states.controllers.mastersalt_master false
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_master_changed="1"
        fi
    fi
}

reconfigure_salt_master() {
    branch_id="$(get_ms_branch|"${SED}" -e "s/changeset://g")"
    master="${1:-${SALT_MASTER_DNS}}"
    master_ip="${2:-${SALT_MASTER_IP}}"
    port="${3:-${SALT_MASTER_PORT}}"
    publish_port="${4:-${SALT_MASTER_PUBLISH_PORT}}"
    salt_master_changed="${salt_master_changed:-"0"}"
    if [ "x${IS_SALT_MASTER}" != "x"];then
        for conf in "${SALT_PILLAR}/salt_minion.sls" "${SALT_PILLAR}/salt.sls";do
            # think to firewall the interfaces, but restricting only to localhost cause
            # more harm than good
            # any way the keys for attackers need to be accepted.
            edit_yaml_file "${conf}" makina-states.controllers.salt_master.settings.interface "${master_ip}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_master_changed="1"
            fi
            edit_yaml_file "${conf}" makina-states.controllers.salt_master.settings.publish_port "${publish_port}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_master_changed="1"
            fi
            edit_yaml_file "${conf}" makina-states.controllers.salt_master.settings.ret_port "${port}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_master_changed="1"
            fi
            edit_yaml_file "${conf}" "${BRANCH_PILLAR_ID}" "${branch_id}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_master_changed="1"
            fi
        done
        for conf in "${CONF_PREFIX}"/master "${CONF_PREFIX}"/master.d/*;do
            if [ -f "${conf}" ];then
                edit_yaml_file "${conf}" interface "${master_ip}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    salt_master_changed="1"
                fi
                edit_yaml_file "${conf}" ret_port "${port}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    salt_master_changed="1"
                fi
                edit_yaml_file "${conf}" publish_port "${publish_port}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    salt_master_changed="1"
                fi
            fi
        done
        edit_yaml_file "${CONF_PREFIX}/grains" makina-states.controllers.salt_master true
        if [ "x${yaml_file_changed}" != "x0" ];then
            salt_master_changed="1"
        fi
    else
        edit_yaml_file "${CONF_PREFIX}/grains" makina-states.controllers.salt_master false
        if [ "x${yaml_file_changed}" != "x0" ];then
            salt_master_changed="1"
        fi
    fi
}

reconfigure_mastersalt_minion() {
    branch_id="$(get_ms_branch|"${SED}" -e "s/changeset://g")"
    setted_id="${1:-$(get_minion_id)}"
    master="${1:-${MASTERSALT_MASTER_DNS}}"
    port="${2:-${%MASTERSALT_MASTER_PORT}}"
    minion_ip="${3:-${MASTERSALT_MINION_IP}}"
    mastersalt_minion_changed="${mastersalt_minion_changed:-"0"}"
    if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
        for i in "${MCONF_PREFIX}/minion_id";do
            if [ -f "${i}" ];then
                echo "${setted_id}" > "${i}"
            fi
        done
        for conf in "${MCONF_PREFIX}/grains" "${MASTERSALT_PILLAR}/mastersalt_minion.sls" "${MASTERSALT_PILLAR}/mastersalt.sls";do
            if [ -e "${conf}" ];then
                touch "${conf}"
            fi
            "${SED}" -i -e "/^    id:/ d" "${conf}"
            edit_yaml_file ${conf} id "${setted_id}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_minion_changed="1"
            fi
            edit_yaml_file ${conf} makina-states.minion_id "${setted_id}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_minion_changed="1"
            fi
        done
        for conf in "${MASTERSALT_PILLAR}/mastersalt_minion.sls" "${MASTERSALT_PILLAR}/mastersalt.sls";do
            edit_yaml_file "${conf}" makina-states.controllers.mastersalt_minion.settings.master "${master}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_minion_changed="1"
            fi
            edit_yaml_file "${conf}" makina-states.controllers.mastersalt_minion.settings.master_port "${port}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_minion_changed="1"
            fi
            edit_yaml_file "${conf}" "${BRANCH_PILLAR_ID}" "${branch_id}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_minion_changed="1"
            fi
            edit_yaml_file "${conf}" makina-states.controllers.mastersalt_minion.settings.interface "${minion_ip}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
        done
        for conf in  "${MCONF_PREFIX}"/minion "${MCONF_PREFIX}"/minion.d/*;do
            if [ -f "${conf}" ];then
                "${SED}" -i -e "/^    id:/ d" "${conf}"
                edit_yaml_file "${conf}" id "${setted_id}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    mastersalt_minion_changed="1"
                fi
                edit_yaml_file "${conf}" makina-states.minion_id "${setted_id}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    mastersalt_minion_changed="1"
                fi
                edit_yaml_file "${conf}" interface "${minion_ip}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    mastersalt_minion_changed="1"
                fi
                edit_yaml_file "${conf}" master "${master}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    mastersalt_minion_changed="1"
                fi
                edit_yaml_file "${conf}" master_port "${port}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    mastersalt_minion_changed="1"
                fi
            fi
        done
        edit_yaml_file "${MCONF_PREFIX}/grains" makina-states.controllers.mastersalt_minion true
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_minion_changed="1"
        fi
    else
        edit_yaml_file "${MCONF_PREFIX}/grains" makina-states.controllers.mastersalt_minion false
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_minion_changed="1"
        fi
    fi
}

reconfigure_salt_minion() {
    branch_id="$(get_ms_branch|"${SED}" -e "s/changeset://g")"
    setted_id="${1:-$(get_minion_id)}"
    master="${1:-${SALT_MASTER_DNS}}"
    port="${2:-${SALT_MASTER_PORT}}"
    salt_minion_changed="${salt_minion_changed:-"0"}"
    if [ "x${IS_SALT_MINION}" != "x" ];then
        for i in "${CONF_PREFIX}/minion_id";do
            if [ -f "${i}" ];then
                echo "${setted_id}" > "${i}"
            fi
        done
        for conf in "${CONF_PREFIX}/grains" "${SALT_PILLAR}/salt_minion.sls" "${SALT_PILLAR}/salt.sls";do
            if [ ! -e "${conf}" ];then
                touch "${conf}"
            fi
            "${SED}" -i -e "/^    id:/ d" "${conf}"
            edit_yaml_file "${conf}" id "${setted_id}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
            edit_yaml_file "${conf}" makina-states.minion_id "${setted_id}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
        done
        for conf in "${SALT_PILLAR}/salt_minion.sls" "${SALT_PILLAR}/salt.sls";do
            edit_yaml_file "${conf}" makina-states.controllers.salt_minion.settings.master "${master}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
            edit_yaml_file "${conf}" makina-states.controllers.salt_minion.settings.master_port "${port}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
            edit_yaml_file "${conf}" "${BRANCH_PILLAR_ID}" "${branch_id}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
            edit_yaml_file "${conf}" makina-states.controllers.salt_minion.settings.interface "${minion_ip}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
        done
        for conf in "${CONF_PREFIX}"/minion "${CONF_PREFIX}"/minion.d/*;do
            if [ -f "${conf}" ];then
                edit_yaml_file "${conf}" id "${setted_id}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    salt_minion_changed="1"
                fi
                edit_yaml_file "${conf}" master "${master}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    salt_minion_changed="1"
                fi
                edit_yaml_file "${conf}" master_port "${port}"
                if [ "x${yaml_file_changed}" != "x0" ];then
                    salt_minion_changed="1"
                fi
            fi
        done
        edit_yaml_file "${CONF_PREFIX}/grains" makina-states.controllers.salt_minion true
        if [ "x${yaml_file_changed}" != "x0" ];then
            salt_minion_changed="1"
        fi
    else
        edit_yaml_file "${CONF_PREFIX}/grains" makina-states.controllers.salt_minion false
        if [ "x${yaml_file_changed}" != "x0" ];then
            salt_minion_changed="1"
        fi
    fi

}

reconfigure_masters() {
    reconfigure_salt_master
    reconfigure_mastersalt_master
}

reconfigure_minions() {
    reconfigure_salt_minion
    reconfigure_mastersalt_minion
}


create_pillars() {
    # create pillars
    SALT_PILLAR_ROOTS="${SALT_PILLAR}"
    if [ "x${IS_MASTERSALT}" != "x" ];then
        SALT_PILLAR_ROOTS="${SALT_PILLAR_ROOTS} ${MASTERSALT_PILLAR}"
    fi

    for pillar_root in ${SALT_PILLAR_ROOTS};do
        if [ ! -e ${pillar_root} ];then
            mkdir -p "${pillar_root}"
            chmod 700 "${pillar_root}"
        fi
        # Create a default custom.sls in the pillar if not present
        if [ ! -f "${pillar_root}/custom.sls" ];then
            debug_msg "creating default ${pillar_root}/custom.sls"
            cat > "${pillar_root}/custom.sls" << EOF
#
# This is a file to drop pillar configuration in
#

EOF
        fi

        # Create a default top.sls in the pillar if not present
        if [ ! -f "${pillar_root}/top.sls" ];then
            debug_msg "creating default ${pillar_root}/top.sls"
            cat > "${pillar_root}/top.sls" << EOF
#
# This is the top pillar configuration file, link here all your
# environment configurations files to their respective minions
#
base:
  '*':
EOF
        fi
        skip_next=""
        if [ "x$(egrep -- "^    - mastersalt(_minion)?[ ]*$" "${pillar_root}/top.sls"|wc -l|${SED} -e "s/ //g")" = "x0" ];then
            skip_next="1"
        fi
        if [ "x${skip_next}" = "x" ];then
            if [ "x$(grep -- "$(get_minion_id)" "${pillar_root}/top.sls"|wc -l|${SED} -e "s/ //g")" = "x0" ];then
                debug_msg "Adding local info to top mastersalt pillar"
                echo >> "${pillar_root}/top.sls"
                echo "  '$(get_minion_id)':">> "${pillar_root}/top.sls"
            fi
        fi
    done
}

create_salt_tops() {
    # Create a default top.sls in the tree if not present
    TOPS_FILES="${SALT_ROOT}/top.sls"
    if [ "x${IS_MASTERSALT}" != "x" ];then
        TOPS_FILES="$TOPS_FILES ${MASTERSALT_ROOT}/top.sls"
    fi
    for topf in $TOPS_FILES;do
        if [ ! -f "${topf}" ];then
            debug_msg "creating default salt's ${topf}"
            cat > "${topf}" << EOF
#
# This is the salt states configuration file, link here all your
# environment states files to their respective minions
#
base:
  '*':
EOF
        fi
        # add makina-state.top if not present
        if [ "x$(egrep -- "- makina-states\.top( |\t)*$" ${topf}|wc -l|${SED} -e "s/ //g")" = "x0" ];then
            debug_msg "Adding makina-states.top to ${topf}"
            "${SED}" -i -e "/['\"]\*['\"]:/ {
a\    - makina-states.top
}" "${topf}"
        fi
    done
}

create_pillar_tops() {
    if [ "x$(grep -- "- custom" "${SALT_PILLAR}/top.sls"|wc -l|${SED} -e "s/ //g")" = "x0" ];then
        debug_msg "Adding custom sls top salt pillar"
        "${SED}" -i -e "/['\"]$(get_minion_id)['\"]:/ {
a\    - custom
}" "${SALT_PILLAR}/top.sls"
    fi
    if [ "x$(grep -- "- salt_minion" ${SALT_PILLAR}/top.sls 2>/dev/null|wc -l|${SED} -e "s/ //g")" = "x0" ];then
        debug_msg "Adding salt to default top salt pillar"
        "${SED}" -i -e "/['\"]\*['\"]:/ {
a\    - salt_minion
}" "${SALT_PILLAR}/top.sls"
        "${SED}" -i -e "/    - salt$/ d" "${SALT_PILLAR}/top.sls"
    fi
    if [ "x$(grep -- "- salt" ${SALT_PILLAR}/top.sls 2>/dev/null|grep -v salt_minion|grep -v minion|wc -l|${SED} -e "s/ //g")" = "x0" ];then
        debug_msg "Adding salt to default top salt pillar"
        "${SED}" -i -e "/['\"]$(get_minion_id)['\"]:/ {
a\    - salt
}" "${SALT_PILLAR}/top.sls"
    fi
    # --------- MASTERSALT
    # Set default mastersalt  pillar
    if [ "x${IS_MASTERSALT}" != "x" ];then
        if [ "x$(grep -- "- custom" "${MASTERSALT_PILLAR}/top.sls"|wc -l|${SED} -e "s/ //g")" = "x0" ];then
            debug_msg "Adding custom sls top mastersalt pillar"
            "${SED}" -i -e "/['\"]$(get_minion_id)['\"]:/ {
a\    - custom
}" "${MASTERSALT_PILLAR}/top.sls"
        fi
        if [ "x$(grep -- "- mastersalt_minion" "${MASTERSALT_PILLAR}/top.sls" 2>/dev/null|wc -l|${SED} -e "s/ //g")" = "x0" ];then
            debug_msg "Adding mastersalt info to top mastersalt pillar"
            "${SED}" -i -e "/['\"]\*['\"]:/ {
a\    - mastersalt_minion
}" "${MASTERSALT_PILLAR}/top.sls"
        "${SED}" -i -e "/    - mastersalt$/ d" "${MASTERSALT_PILLAR}/top.sls"
        fi
        if [ "x$(grep -- "- mastersalt$" "${MASTERSALT_PILLAR}/top.sls" 2>/dev/null|wc -l|grep -v mastersalt_minion|${SED} -e "s/ //g")" = "x0" ];then
            debug_msg "Adding mastersalt info to top mastersalt pillar"
            "${SED}" -i -e "/['\"]$(get_minion_id)['\"]:/ {
a\    - mastersalt
}" "${MASTERSALT_PILLAR}/top.sls"
        fi
    fi
}

maybe_wire_reattached_conf() {

    # install salt cloud keys &  reconfigure any preprovisionned daemons
    if [ "x${SALT_REATTACH}" != "x" ];then
        bs_log "SaltCloud mode: killing daemons"
        if [ "x$(is_lxc)" != "x0" ];then
            regenerate_openssh_keys
        fi
        kill_ms_daemons
        # remove any provisionned init overrides
        if [ "x$(find /etc/init/*salt*.override 2>/dev/null|wc -l|${SED} "s/ //g")" != "x0" ];then
            bs_log "SaltCloud mode: removing init stoppers"
            rm -fv /etc/init/*salt*.override
        fi
        bs_log "SaltCloud mode: Resetting some configurations"
        rm -f "${CONF_PREFIX}/pki/minion/minion_master.pub"
        # regenerate keys for the local master
        if [ "x$(which salt-key 2>/dev/null)" != "x" ];then
            "${SALT_MS}"/bin/salt-key -c /etc/salt --gen-keys=master --gen-keys-dir="${CONF_PREFIX}/pki/master"
        fi
        if [ "x${IS_MASTERSALT}" != "x" ];then
            bs_log "SaltCloud mode: Resetting some mastersalt configurations"
            minion_dest="${MCONF_PREFIX}/pki/minion"
            master_dest="${MCONF_PREFIX}/pki/master"
            __install "${SALT_REATTACH_DIR}/minion.pem" "${minion_dest}/minion.pem"
            __install "${SALT_REATTACH_DIR}/minion.pub" "${minion_dest}/minion.pub"
            rm -f "${MCONF_PREFIX}/pki/minion/minion_master.pub"
            # resetting local salt-minion's key
            find "${CONF_PREFIX}/pki/master" -name $(get_minion_id) 2>/dev/null|while read fic;do rm -fv "${fic}";done
        fi
        bs_log "SaltCloud mode: Installing keys"
        minion_dest="${CONF_PREFIX}/pki/minion"
        master_dest="${CONF_PREFIX}/pki/master"
        __install "${SALT_REATTACH_DIR}/minion.pem" "${minion_dest}/minion.pem"
        __install "${SALT_REATTACH_DIR}/minion.pub" "${minion_dest}/minion.pub"
        __install "${SALT_REATTACH_DIR}/minion.pub" "${master_dest}/minions/$(get_minion_id)"
        __install "${SALT_REATTACH_DIR}/master.pem" "${master_dest}/master.pem"
        __install "${SALT_REATTACH_DIR}/master.pub" "${master_dest}/master.pub"
        for i in "${MASTERSALT_PILLAR}/mastersalt.sls" "${SALT_PILLAR}/salt.sls";do
            if [ -e "$i" ];then
                bs_log "SaltCloud mode: removing ${i} default conf for it to be resetted"
                rm -f "${i}"
            fi
        done
    fi
}

create_core_conf() {
    # create /etc/salt directory
    if [ "x${IS_SALT}" != "x" ] || [ "${IS_MASTERSALT}" != "x" ];then
        if [ ! -e "${CONF_PREFIX}" ];then mkdir "${CONF_PREFIX}";fi
        if [ ! -e "${CONF_PREFIX}/master.d" ];then mkdir "${CONF_PREFIX}/master.d";fi
        if [ ! -e "${CONF_PREFIX}/minion.d" ];then mkdir "${CONF_PREFIX}/minion.d";fi
        if [ ! -e "${CONF_PREFIX}/pki/master/minions" ];then mkdir -p "${CONF_PREFIX}/pki/master/minions";fi
        if [ ! -e "${CONF_PREFIX}/pki/minion" ];then mkdir -p "${CONF_PREFIX}/pki/minion";fi
        for d in \
            /var/run/salt/salt-master\
            /var/run/salt/salt-minion\
            /var/cache/salt-minion\
            /var/cache/salt-master\
            /var/log/salt;do
            if [ ! -e "${d}" ];then
                mkdir -pv "${d}"
            fi
        done
        salt_root="${SALT_ROOT}"
        conf_prefix="${CONF_PREFIX}"
        # salt-master
        touch "${CONF_PREFIX}/grains"
        if [ ! -e "${CONF_PREFIX}/master" ];then
            cat > "${CONF_PREFIX}/master" << EOF
pki_dir: ${CONF_PREFIX}/pki/master
cachedir: /var/cache/salt/master
conf_file: ${CONF_PREFIX}/master
sock_dir: /var/run/salt/master
log_file: /var/log/salt/salt-master
pidfile: /var/run/salt-master.pid
file_roots: {"base":["${SALT_ROOT}"]}
pillar_roots: {"base":["${SALT_PILLAR}"]}
EOF
            ${SED} -re \
                "s|\{salt_root\}|${salt_root}|g"\
                "${salt_root}/makina-states/mc_states/modules_dirs.json" \
                | ${SED} -re "s/^[{}]$//g" \
                >> "${conf_prefix}/master"
        fi

    fi

    # salt-minion
    if [ ! -e "${CONF_PREFIX}/minion" ];then
        cat > "${CONF_PREFIX}/minion" << EOF
pki_dir: ${CONF_PREFIX}/pki/minion
cachedir: /var/cache/salt/minion
conf_file: ${CONF_PREFIX}/minion
sock_dir: /var/run/salt/minion
log_file: /var/log/salt/salt-minion
pidfile: /var/run/salt/salt-minion.pid
file_roots: {"base":["${SALT_ROOT}"]}
pillar_roots: {"base":["${SALT_PILLAR}"]}
EOF
        ${SED} -re \
            "s|\{salt_root\}|${salt_root}|g"\
            "${salt_root}/makina-states/mc_states/modules_dirs.json" \
            | ${SED} -re "s/^[{}]$//g" \
            >> "${conf_prefix}/minion"
    fi

    # create /etc/mastersalt
    salt_root="${MASTERSALT_ROOT}"
    conf_prefix="${MCONF_PREFIX}"
    if [ "x${IS_MASTERSALT}" != "x" ];then
        for d in \
            /var/run/mastersalt/mastersalt-master\
            /var/run/mastersalt/mastersalt-minion\
            /var/cache/mastersalt/mastersalt-minion\
            /var/cache/mastersalt/mastersalt-master\
            /var/log/mastersalt;do
            if [ ! -e "${d}" ];then
                mkdir -pv "${d}"
            fi
        done
        if [ ! -e "${MCONF_PREFIX}" ];then mkdir "${MCONF_PREFIX}";fi
        if [ ! -e "${MCONF_PREFIX}/master.d" ];then mkdir "${MCONF_PREFIX}/master.d";fi
        if [ ! -e "${MCONF_PREFIX}/minion.d" ];then mkdir "${MCONF_PREFIX}/minion.d";fi
        if [ ! -e "${MCONF_PREFIX}/pki/master" ];then mkdir -p "${MCONF_PREFIX}/pki/master";fi
        if [ ! -e "${MCONF_PREFIX}/pki/minion" ];then mkdir -p "${MCONF_PREFIX}/pki/minion";fi

        # mastersalt-master
        touch "${MCONF_PREFIX}/grains"
        if [ ! -e "${MCONF_PREFIX}/master" ];then
            cat > "${MCONF_PREFIX}/master" << EOF
pki_dir: ${MCONF_PREFIX}/pki/master
conf_file: ${MCONF_PREFIX}/master
cachedir: /var/cache/mastersalt/mastersalt-master
sock_dir: /var/run/mastersalt/mastersalt-master
log_file: /var/log/mastersalt/mastersalt-master
pidfile: /var/run/mastersalt-master.pid
file_roots: {"base":["${MASTERSALT_ROOT}"]}
pillar_roots: {"base":["${MASTERSALT_PILLAR}"]}
EOF
        ${SED} -re \
            "s|\{salt_root\}|${salt_root}|g"\
            "${salt_root}/makina-states/mc_states/modules_dirs.json" \
            | ${SED} -re "s/^[{}]$//g" \
            >> "${conf_prefix}/master"
        fi

        # mastersalt-minion
        if [ ! -e "${MCONF_PREFIX}/minion" ];then
            cat > "${MCONF_PREFIX}/minion" << EOF
pki_dir: ${MCONF_PREFIX}/pki/minion
cachedir: /var/cache/mastersalt/minion
conf_file: ${MCONF_PREFIX}/minion
sock_dir: /var/run/mastersalt/minion
log_file: /var/log/mastersalt/mastersalt-minion
pidfile: /var/run/mastersalt-minion.pid
file_roots: {"base":["${MASTERSALT_ROOT}"]}
pillar_roots: {"base":["${MASTERSALT_PILLAR}"]}
EOF
        ${SED} -re \
            "s|\{salt_root\}|${salt_root}|g"\
            "${salt_root}/makina-states/mc_states/modules_dirs.json" \
            | ${SED} -re "s/^[{}]$//g" \
            >> "${conf_prefix}/minion"
        fi
    fi
}

create_salt_skeleton() {
    create_core_conf
    create_pillars
    create_salt_tops
    create_pillar_tops
    exit 1
    maybe_wire_reattached_conf
    reconfigure_masters
    reconfigure_minions
}

# ------------ SALT INSTALLATION PROCESS

filter_host_pids() {
    if [ "x$(is_lxc)" != "x0" ];then
        echo "${@}"
    else
        for pid in ${@};do
            if [ "x$(grep -q lxc /proc/${pid}/cgroup 2>/dev/null;echo "${?}")" != "x0" ];then
                 echo ${pid}
             fi
         done
    fi
}

mastersalt_master_processes() {
    filter_host_pids $(${PS} aux|grep salt-master|grep -v deploy.sh|grep -v boot-salt|grep -v bootstrap.sh|grep mastersalt|grep -v grep|awk '{print $2}')|wc -w|${SED} -e "s/ //g"
}

mastersalt_minion_processes() {
    filter_host_pids $(${PS} aux|grep salt-minion|grep -v deploy.sh|grep -v boot-salt|grep -v bootstrap.sh|grep mastersalt|grep -v grep|awk '{print $2}')|wc -w|${SED} -e "s/ //g"
}

master_processes() {
    filter_host_pids $(${PS} aux|grep salt-master|grep -v deploy.sh|grep -v boot-salt|grep -v bootstrap.sh|grep -v mastersalt|grep -v grep|awk '{print $2}')|wc -w|${SED} -e "s/ //g"
}


minion_processes() {
    filter_host_pids $(${PS} aux|grep salt-minion|grep -v deploy.sh|grep -v boot-salt|grep -v bootstrap.sh|grep -v mastersalt|grep -v grep|awk '{print $2}')|wc -w|${SED} -e "s/ //g"
}

lazy_start_salt_daemons() {
    if [ "x${IS_SALT_MASTER}" != "x" ];then
        if [ "x$(master_processes)" = "x0" ] || [ "x${salt_master_changed}" = "x1" ] ;then
            restart_local_masters
            sleep 2
        fi
        if [ "x$(get_local_salt_mode)" != "xmasterless" ] && [ "x$(master_processes)" = "x0" ];then
            die "Salt Master start failed"
        fi
    fi
    if [ "x${IS_SALT_MINION}" != "x" ];then
        if [ "x$(minion_processes)" = "x0" ] || [ "x${salt_minion_changed}" = "x1" ];then
            restart_local_minions
            if [ "x$(get_local_salt_mode)" != "xmasterless" ];then

                if [ "x${SALT_REATTACH}" = "x" ];then
                    sleep 1
                else
                    sleep 2
                fi
                if [ "x$(minion_processes)" = "x0" ];then
                    die "Salt Minion start failed"
                fi
            fi
        fi
    fi
}

gen_mastersalt_keys() {
    if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
        if [ ! -e "${MCONF_PREFIX}/pki/master/master.pub" ];then
            bs_log "Generating mastersalt master key"
            "${MASTERSALT_MS}/bin/salt-key" -c "${MCONF_PREFIX}" --gen-keys=master --gen-keys-dir="${MCONF_PREFIX}/pki/master"
            BS_MS_ASSOCIATION_RESTART_MASTER="1"
        fi
    fi
    if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
        if [ ! -e "${MCONF_PREFIX}/pki/minion/minion.pub" ];then
            bs_log "Generating mastersalt minion key"
            "${MASTERSALT_MS}/bin/salt-key" -c "${MCONF_PREFIX}" --gen-keys=minion --gen-keys-dir="${MCONF_PREFIX}/pki/minion"
            BS_MS_ASSOCIATION_RESTART_MINION="1"
        fi
    fi
    if [ "x${IS_MASTERSALT_MINION}" != "x" ]\
        && [ "x${IS_MASTERSALT_MASTER}" != "x" ]\
        && [ -e "${MCONF_PREFIX}/pki/minion/minion.pub" ];then
        BS_MS_ASSOCIATION_RESTART_MINION="1"
        BS_MS_ASSOCIATION_RESTART_MASTER="1"
        __install "${MCONF_PREFIX}/pki/minion/minion.pub" "${MCONF_PREFIX}/pki/master/minions/$(get_minion_id)"
        __install "${MCONF_PREFIX}/pki/master/master.pub" "${MCONF_PREFIX}/pki/minion/minion_master.pub"
    fi
}

gen_salt_keys() {
    if [ "x${IS_SALT_MASTER}" != "x" ];then
        if [ ! -e "${CONF_PREFIX}/pki/master/master.pub" ];then
            bs_log "Generating salt minion key"
            "${SALT_MS}/bin/salt-key" -c "${CONF_PREFIX}" --gen-keys=master --gen-keys-dir=${CONF_PREFIX}/pki/master
            BS_ASSOCIATION_RESTART_MASTER="1"
        fi
    fi
    # in saltcloude mode, keys are already providen
    if [ "x${SALT_REATTACH}" = "x" ];then
        if [ "x${IS_SALT_MINION}" != "x" ];then
            if [ ! -e "${CONF_PREFIX}/pki/minion/minion.pub" ];then
                bs_log "Generating salt minion key"
                BS_ASSOCIATION_RESTART_MINION="1"
                "${SALT_MS}/bin/salt-key" -c "${CONF_PREFIX}" --gen-keys=minion --gen-keys-dir=${CONF_PREFIX}/pki/minion
            fi
        fi
    fi
    if [ "x${IS_SALT_MINION}" != "x" ]\
       && [ "x${IS_SALT_MASTER}" != "x" ]\
       && [ -e "${CONF_PREFIX}/pki/minion/minion.pub" ];then
        __install "${CONF_PREFIX}/pki/minion/minion.pub" "${CONF_PREFIX}/pki/master/minions/$(get_minion_id)"
        __install "${CONF_PREFIX}/pki/master/master.pub" "${CONF_PREFIX}/pki/minion/minion_master.pub"
        BS_ASSOCIATION_RESTART_MASTER="1"
        BS_ASSOCIATION_RESTART_MINION="1"
    fi
}


install_salt_daemons() {
    # --------- check if we need to run salt setup's
    RUN_SALT_BOOTSTRAP="${SALT_REBOOTSTRAP}"
    if [ "x${SALT_MASTER_DNS}" = "xlocalhost" ];then
        if  [ ! -e "${CONF_PREFIX}/pki/master/master.pem" ]\
            || [ ! -e "${CONF_PREFIX}/master.d/00_global.conf" ];then
            RUN_SALT_BOOTSTRAP="1"
        fi
    fi
    # regenerate keys if missings, but only if we have salt-key yet
    if [ "x$(which salt-key 2>/dev/null)" != "x" ];then
        gen_salt_keys
    fi
    if     [ ! -e "$CONF_PREFIX" ]\
        || [ ! -e "${CONF_PREFIX}/minion.d/00_global.conf" ]\
        || [ -e "${SALT_MS}/.rebootstrap" ]\
        || [ "x$(grep makina-states.controllers.salt_ "${CONF_PREFIX}/grains" 2>/dev/null |wc -l|${SED} -e "s/ //g")" = "x0" ]\
        || [ ! -e "${CONF_PREFIX}/pki/minion/minion.pem" ]\
        || [ ! -e "${BIN_DIR}/salt" ]\
        || [ ! -e "${BIN_DIR}/salt-call" ]\
        || [ ! -e "${BIN_DIR}/salt-cp" ]\
        || [ ! -e "${BIN_DIR}/salt-key" ]\
        || [ ! -e "${BIN_DIR}/salt-master" ]\
        || [ ! -e "${BIN_DIR}/salt-minion" ]\
        || [ ! -e "${BIN_DIR}/salt-ssh" ]\
        || [ ! -e "${BIN_DIR}/salt-syndic" ]\
        || [ ! -e "${CONF_PREFIX}/pki/minion/minion.pem" ];then
        if [ -e "${SALT_MS}/.rebootstrap" ];then
            rm -f "${SALT_MS}/.rebootstrap"
        fi
        RUN_SALT_BOOTSTRAP="1"
    fi
    if [ "x${IS_SALT_MASTER}" != "x" ];then
        if [ ! -e "${ETC_INIT}/salt-master.conf" ]\
            && [ ! -e "${ETC_INIT}.d/salt-master" ];then
            RUN_SALT_BOOTSTRAP="1"
        fi
    fi
    if [ "x${IS_SALT_MINION}" != "x" ];then
        if [ ! -e "${ETC_INIT}/salt-minion.conf" ]\
            && [ ! -e "${ETC_INIT}.d/salt-minion" ];then
            RUN_SALT_BOOTSTRAP="1"
        fi
    fi

    # --------- SALT install
    if [ "x${RUN_SALT_BOOTSTRAP}" != "x" ];then
        ds=y
        # kill salt running daemons if any
        if [ "x${SALT_MASTER_DNS}" = "xlocalhost" ];then
            killall_local_masters
        fi
        if [ "x${IS_SALT_MINION}" != "x" ];then
            killall_local_minions
        fi

        bs_log "Boostrapping salt"

        ${SED} -i -e "/makina-states.nodetypes.$(get_salt_nodetype):/ d"  "${CONF_PREFIX}/grains"
        echo "makina-states.nodetypes.$(get_salt_nodetype): true" >> "${CONF_PREFIX}/grains"
        run_salt_bootstrap "${salt_bootstrap_nodetype}"

        # run salt master setup
        if [ "x${IS_SALT_MASTER}" != "x" ];then
            run_salt_bootstrap "${salt_bootstrap_master}"
        fi

        # run salt minion setup
        if [ "x${IS_SALT_MINION}" != "x" ];then
            run_salt_bootstrap "${salt_bootstrap_minion}"
        fi

        gen_salt_keys

        # restart salt daemons
        if [ "x${IS_SALT_MASTER}" != "x" ];then
            # restart salt salt-master after setup
            bs_log "Forcing salt master restart"
            restart_local_masters
            if [ "x$(get_local_salt_mode)" != "xmasterless" ];then
                sleep 10
            fi
        fi
        # restart salt minion
        if [ "x${IS_SALT_MINION}" != "x" ];then
            bs_log "Forcing salt minion restart"
            restart_local_minions
        fi
        SALT_BOOT_NOW_INSTALLED="y"
    else
        if [ "x${QUIET}" = "x" ];then
            bs_log "Skip salt installation, already done"
        fi
    fi
    lazy_start_salt_daemons
}

kill_pids() {
    for i in ${@};do
        if [ "x$x{i}" != "x" ];then
            kill -9 ${i}
        fi
    done
}

killall_local_mastersalt_masters() {
    if [ ! -e "${ALIVE_MARKER}" ];then
        kill_pids $(filter_host_pids $(${PS} aux|egrep "salt-(master|syndic)"|grep -v deploy.sh|grep -v bootstrap.sh|grep -v boot-salt|grep mastersalt|awk '{print $2}')) 1>/dev/null 2>/dev/null
    fi
}

killall_local_mastersalt_minions() {
    if [ ! -e "${ALIVE_MARKER}" ];then
        kill_pids $(filter_host_pids $(${PS} aux|egrep "salt-(minion)"|grep -v deploy.sh|grep -v bootstrap.sh|grep -v boot-salt|grep mastersalt|awk '{print $2}')) 1>/dev/null 2>/dev/null
    fi
}

killall_local_masters() {
    if [ ! -e "${ALIVE_MARKER}" ];then
        kill_pids $(filter_host_pids $(${PS} aux|egrep "salt-(master|syndic)"|grep -v deploy.sh|grep -v bootstrap.sh|grep -v boot-salt|grep -v mastersalt|awk '{print $2}')) 1>/dev/null 2>/dev/null
    fi
}

killall_local_minions() {
    if [ ! -e "${ALIVE_MARKER}" ];then
        kill_pids $(filter_host_pids $(${PS} aux|egrep "salt-(minion)"|grep -v deploy.sh|grep -v bootstrap.sh|grep -v boot-salt|grep -v mastersalt|awk '{print $2}')) 1>/dev/null 2>/dev/null
    fi
}

restart_local_mastersalt_masters() {
    upgrade_from_buildout
    if [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then
        stop_and_disable_service mastersalt-master
    else
        enable_service mastersalt-master
        if [ ! -e "${ALIVE_MARKER}" ] && [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            service_ mastersalt-master stop
            killall_local_mastersalt_masters
            service_ mastersalt-master restart
        fi
    fi
    mastersalt_master_changed="0"
}

restart_local_mastersalt_minions() {
    upgrade_from_buildout
    if [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then
        killall_local_mastersalt_minions
        stop_and_disable_service mastersalt-minion
    else
        enable_service salt-minion
        if [ ! -e "${ALIVE_MARKER}" ] && [ "x${IS_MASTERSALT_MINION}" != "x" ];then
            service_ mastersalt-minion stop
            killall_local_mastersalt_minions
            service_ mastersalt-minion restart
        fi
    fi
    mastersalt_minion_changed="0"
}

restart_local_masters() {
    upgrade_from_buildout
    if [ "x$(get_local_salt_mode)" = "xmasterless" ];then
        stop_and_disable_service salt-master
    else
        enable_service salt-master
        if [ ! -e "${ALIVE_MARKER}" ] && [ "x${IS_SALT_MASTER}" != "x" ];then
            service_ salt-master stop
            killall_local_masters
            service_ salt-master restart
        fi
    fi
    salt_master_changed="0"
}

restart_local_minions() {
    upgrade_from_buildout
    if [ "x$(get_local_salt_mode)" = "xmasterless" ];then
        stop_and_disable_service salt-minion
    else
        enable_service salt-minion
        if [ ! -e "${ALIVE_MARKER}" ] && [ "x${IS_SALT_MINION}" != "x" ];then
            service_ salt-minion stop
            killall_local_minions
            service_ salt-minion restart
        fi
    fi
    salt_minion_changed="0"
}

salt_ping_test() {
    # test in a subshell as this can be bloquant
    # salt cloud would then fail badly on this
    rm -f "${SALT_BOOT_LOCK_FILE}" "${LAST_RETCODE_FILE}"
    (
        touch "${SALT_BOOT_LOCK_FILE}";
        salt_call_wrapper test.ping 1>/dev/null 2>/dev/null;
        echo "${last_salt_retcode}" > "${LAST_RETCODE_FILE}"
    )&
    testpid=$!
    # wait for one minute for the test to be ok
    for i in `seq 60`;do
        if [ ! -e "${LAST_RETCODE_FILE}" ];then
            sleep 1
        else
          last_salt_retcode="$(cat ${LAST_RETCODE_FILE} 2>/dev/null)"
          if [ "x${last_salt_retcode}" = "x" ];then
              last_salt_retcode="0"
          fi
          rm -f "${SALT_BOOT_LOCK_FILE}"
        fi
    done
    if [ -e "${SALT_BOOT_LOCK_FILE}" ];then
        kill -9 ${testpid}
        echo 256
    fi
    rm -f "${SALT_BOOT_LOCK_FILE}" "${LAST_RETCODE_FILE}"
    echo "${last_salt_retcode}"
}

mastersalt_ping_test() {
    # test in a subshell as this can be bloquant
    # salt cloud would then fail badly on this
    rm -f "${SALT_BOOT_LOCK_FILE}" "${LAST_RETCODE_FILE}"
    (
        touch "${SALT_BOOT_LOCK_FILE}";
        mastersalt_call_wrapper test.ping 1>/dev/null 2>/dev/null;
        echo "${last_salt_retcode}" > "${LAST_RETCODE_FILE}"
    )&
    testpid=$!
    # wait for one minute for the test to be ok
    for i in `seq 60`;do
        if [ ! -e "${LAST_RETCODE_FILE}" ];then
            sleep 1
        else
          last_salt_retcode="$(cat ${LAST_RETCODE_FILE})"
          rm -f "${SALT_BOOT_LOCK_FILE}"
        fi
    done
    if [ -e "${SALT_BOOT_LOCK_FILE}" ];then
        kill -9 ${testpid}
        echo 256
    fi
    rm -f "${SALT_BOOT_LOCK_FILE}" "${LAST_RETCODE_FILE}"
    echo "${last_salt_retcode}"
}

minion_challenge() {
    if [ "x${IS_SALT_MINION}" = "x" ];then return;fi
    if [ "x$(get_local_salt_mode)" = "xmasterless" ];then
        challenged_me="y"
        resultping="0"
        return;
    fi
    challenged_ms=""
    global_tries="30"
    inner_tries="5"
    for i in `seq ${global_tries}`;do
        if [ "x${SALT_MASTER_DNS}" = "xlocalhost" ] && [ "x$(hostname|${SED} -e "s/.*devhost.*/match/")" = "xmatch" ];then
            debug_msg "Forcing salt master restart"
            restart_local_masters
            sleep 10
        fi
        restart_local_minions
        resultping="1"
        for j in `seq ${inner_tries}`;do
            resultping="$(salt_ping_test)"
            if [ "x${resultping}" != "x0" ];then
                bs_yellow_log " sub challenge try (${i}/${global_tries}) (${j}/${inner_tries})"
                sleep 1
            else
                break
            fi
        done
        if [ "x${resultping}" != "x0" ];then
            bs_log "Failed challenge salt keys on master, retry ${i}/${global_tries}"
            challenged_ms=""
        else
            challenged_ms="y"
            bs_log "Successfull challenge salt keys on master"
            break
        fi
    done
}

mastersalt_minion_challenge() {
    if [ "x${IS_MASTERSALT_MINION}" = "x" ];then return;fi
    if [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then
        challenged_me="y"
        resultping="0"
        return;
    fi
    challenged_ms=""
    global_tries="30"
    inner_tries="5"
    for i in `seq ${global_tries}`;do
        if [ "x${MASTERSALT}" = "xlocalhost" ] && [ "x$(hostname|${SED} -e "s/.*devhost.*/match/")" = "xmatch" ];then
            debug_msg "Forcing salt mastersalt master restart"
            restart_local_mastersalt_masters
            sleep 10
        fi
        restart_local_mastersalt_minions
        resultping="1"
        for j in `seq ${inner_tries}`;do
            resultping="$(mastersalt_ping_test)"
            if [ "x${resultping}" != "x0" ];then
                bs_yellow_log " sub challenge try (${i}/${global_tries}) (${j}/${inner_tries})"
                sleep 1
            else
                break
            fi
        done
        if [ "x${resultping}" != "x0" ];then
            bs_log "Failed challenge mastersalt keys on ${MASTERSALT}, retry ${i}/${global_tries}"
            challenged_ms=""
        else
            challenged_ms="y"
            bs_log "Successfull challenge mastersalt keys on ${MASTERSALT}"
            break
        fi
    done
}

salt_master_connectivity_check() {
    if [ "x$(get_local_salt_mode)" != "xmasterless" ];then
        if [ "x$(check_connectivity ${SALT_MASTER_IP} ${SALT_MASTER_PORT} 30)" != "x0" ];then
            die "SaltMaster is unreachable (${SALT_MASTER_IP}/${SALT_MASTER_PORT})"
        fi
    fi
}

mastersalt_master_connectivity_check() {
    if [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then return;fi
    if [ "x$(check_connectivity ${MASTERSALT} ${MASTERSALT_MASTER_PORT} 30)" != "x0" ];then
        die "MastersaltMaster is unreachable (${MASTERSALT}/${MASTERSALT_MASTER_PORT})"
    fi
}

challenge_message() {
    minion_id="$(get_minion_id)"
    if [ "x${QUIET}" = "x" ]; then
        bs_log "****************************************************************"
        bs_log "     GO ACCEPT THE KEY ON SALT_MASTER  (${SALT_MASTER_IP}) !!! "
        bs_log "     You need on this box to run salt-key -y -a ${minion_id}"
        bs_log "****************************************************************"
    fi
}

get_delay_time() {
    if [ "x${SALT_NODETYPE}" = "xtravis" ];then
        echo 15
    else
        echo 3
    fi
}

make_association() {
    if [ "x${IS_SALT_MINION}" = "x" ];then return;fi
    if [ "x$(get_local_salt_mode)" = "xmasterless" ];then
        registered="1"
        minion_id="$(get_minion_id)"
    fi
    minion_keys="$(find ${CONF_PREFIX}/pki/master/minions -type f 2>/dev/null|wc -l|grep -v ${SED}|${SED} -e "s/ //g")"
    minion_id="$(get_minion_id)"
    registered=""
    debug_msg "Entering association routine"
    minion_id="$(get_minion_id)"
    if [ "x${QUIET}" = "x" ];then
        bs_log "If the bootstrap program seems to block here"
        challenge_message
    fi
    debug_msg "ack"
    if [ "x${SALT_NODETYPE}" = "xtravis" ];then
        set -x
        service_ salt-minion restart
    #   . /etc/profile
    #   for i in `seq 4`;do
    #       #( salt-minion -lall )&
    #       sleep 15
    #       uname -ar
    #   done
    #    cat /etc/init/salt*.conf
    #    cat /var/log/upstart/salt* /var/log/salt/*minion*
    #    ls -lrt /var/log/salt
    #    ls -lrt /var/log/upstart
    #    cat /var/log/salt/salt-master
    #    cat /var/log/salt/salt-minion
         set +x
    fi
    if [ "x${BS_ASSOCIATION_RESTART_MASTER}" != "x" ];then
        restart_local_masters
        sleep 10
    fi
    if [ "x${BS_ASSOCIATION_RESTART_MINION}" != "x" ];then
        restart_local_minions
    fi
    if [ "x$(master_processes)" = "x0" ] && [ "x${IS_SALT_MASTER}" != "x" ];then
        restart_local_masters
    fi
    if [ "x$(minion_processes)" = "x0" ];then
        restart_local_minions
        if [ "x$(get_local_salt_mode)" != "xmasterless" ];then
            sleep $(get_delay_time)
        fi
        travis_sys_info
        minion_id="$(get_minion_id)"
        if [ "x${minion_id}" = "x" ];then
            die "Minion did not start correctly, the minion_id cache file is always empty"
        fi
    fi
    # only accept key on fresh install (no keys stored)
    if [ "x$(salt_ping_test)" = "x0" ];\
    then
        debug_msg "Salt minion \"${minion_id}\" already registered on master"
        minion_id="$(get_minion_id)"
        registered="1"
        salt_echo "changed=false comment='salt minion already registered'"
    else
        if [ "x${SALT_MASTER_DNS}" = "xlocalhost" ];then
            debug_msg "Forcing salt master restart"
            restart_local_masters
            sleep 10
        fi
        if [ "x${SALT_MASTER_DNS}" != "xlocalhost" ] &&  [ "x${SALT_NO_CHALLENGE}" = "x" ];then
            challenge_message
            bs_log " We are going to wait 10 minutes for you to setup the minion on mastersalt and"
            bs_log " setup an entry for this specific minion"
            bs_log " export SALT_NO_CHALLENGE=1 to remove the temporisation (enter to continue when done)"
            interactive_tempo $((10 * 60))
        else
            bs_log "  [*] No temporisation for challenge, trying to spawn the minion"
            if [ "x${SALT_MASTER_DNS}" = "xlocalhost" ];then
                "${SALT_MS}/bin/salt-key" -c "${CONF_PREFIX}" -y -a "${minion_id}"
                ret="${?}"
                if [ "x${ret}" != "x0" ];then
                    bs_log "Failed accepting keys"
                    warn_log
                    exit 1
                else
                    bs_log "Accepted key"
                fi
            fi
        fi
        debug_msg "Forcing salt minion restart"
        restart_local_minions
        gen_salt_keys
        salt_master_connectivity_check 20
        bs_log "Waiting for salt minion key hand-shake"
        minion_id="$(get_minion_id)"
        if [ "x$(salt_ping_test)" = "x0" ] && [ "x${minion_keys}" != "x0" ];then
            # sleep 15 seconds giving time for the minion to wake up
            bs_log "Salt minion \"${minion_id}\" registered on master"
            registered="1"
            salt_echo "changed=yes comment='salt minion already registered'"
        else
            minion_challenge
            if [ "x${challenged_ms}" = "x" ];then
                bs_log "Failed accepting salt key on master for ${minion_id}"
                warn_log
                exit 1
            fi
            minion_id="$(get_minion_id)"
            registered="1"
            salt_echo "changed=yes comment='salt minion already registered'"
        fi
        if [ "x${registered}" = "x" ];then
            bs_log "Failed accepting salt key on ${SALT_MASTER_IP} for ${minion_id}"
            warn_log
            exit 1
        fi
    fi
}

challenge_mastersalt_message() {
    minion_id="$(get_minion_id)"
    if [ "x${QUIET}" = "x" ]; then
        bs_log "****************************************************************"
        bs_log "    GO ACCEPT THE KEY ON MASTERSALT (${MASTERSALT}) !!! "
        bs_log "    You need on this box to run mastersalt-key -y -a ${minion_id}"
        bs_log "****************************************************************"
    fi
}

salt_echo() {
    if [ "x${QUIET}" = "x" ];then
        echo "${@}"
    fi
}

make_mastersalt_association() {
    if [ "x${IS_MASTERSALT_MINION}" = "x" ];then return;fi
    minion_id="$(cat "${CONF_PREFIX}/minion_id" 1>/dev/null 2>/dev/null)"
    registered=""
    debug_msg "Entering mastersalt association routine"
    minion_id="$(get_minion_id)"
    if [ "x${QUIET}" = "x" ];then
        bs_log "If the bootstrap program seems to block here"
        challenge_mastersalt_message
    fi
    debug_msg "ack"
    if [ "x${minion_id}" = "x" ];then
        bs_yellow_log "Minion did not start correctly, the minion_id cache file is empty, trying to restart"
        restart_local_mastersalt_minions
        sleep $(get_delay_time)
        travis_sys_info
        minion_id="$(get_minion_id)"
        if [ "x${minion_id}" = "x" ];then
            die "Minion did not start correctly, the minion_id cache file is always empty"
        fi
    fi
    if [ "x$(mastersalt_ping_test)" = "x0" ];then
        debug_msg "Mastersalt minion \"${minion_id}\" already registered on ${MASTERSALT}"
        salt_echo "changed=false comment='mastersalt minion already registered'"
    else
        if [ "x$(mastersalt_master_processes)" = "x0" ] && [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            restart_local_mastersalt_masters
        fi
        if [ "x${MASTERSALT_MASTER_DNS}" != "xlocalhost" ] && [ "x${MASTERSALT_NO_CHALLENGE}" != "x" ];then
            challenge_mastersalt_message
            bs_log " We are going to wait 10 minutes for you to setup the minion on mastersalt and"
            bs_log " setup an entry for this specific minion"
            bs_log " export MASTERSALT_NO_CHALLENGE=1 to remove the temporisation (enter to continue when done)"
            interactive_tempo $((10*60))
        else
            bs_log "  [*] No temporisation for challenge, trying to spawn the mastersalt minion"
            # in case of a local mastersalt, auto accept the minion key
            if [ "x${MASTERSALT_MASTER_DNS}" = "xlocalhost" ];then
                mastersalt-key -y -a "${minion_id}"
                ret="${?}"
                if [ "x${ret}" != "x0" ];then
                    bs_log "Failed accepting mastersalt keys"
                    warn_log
                    exit 1
                else
                    bs_log "Accepted mastersalt key"
                fi
            fi
        fi

        debug_msg "Forcing mastersalt minion restart"
        restart_local_mastersalt_minions
        #if [ "x${BS_MS_ASSOCIATION_RESTART_MASTER}" != "x" ];then
        #    restart_local_mastersalt_masters
        #    sleep 10
        #fi
        #if [ "x${BS_MS_ASSOCIATION_RESTART_MINION}" != "x" ];then
        #    restart_local_mastersalt_minions
        #fi
        gen_mastersalt_keys
        mastersalt_master_connectivity_check
        bs_log "Waiting for mastersalt minion key hand-shake"
        minion_id="$(get_minion_id)"
        mastersalt_call_wrapper test.ping -lall
        if [ "x$(mastersalt_ping_test)" = "x0" ];then
            salt_echo "changed=yes comment='mastersalt minion registered'"
            bs_log "Mastersalt minion \"${minion_id}\" registered on master"
            registered="1"
            salt_echo "changed=yes comment='salt minion registered'"
        else
            mastersalt_minion_challenge
            if [ "x${challenged_ms}" = "x" ];then
                bs_log "Failed accepting salt key on master for ${minion_id}"
                warn_log
                exit 1
            fi
            minion_id="$(get_minion_id)"
            registered="1"
            salt_echo "changed=yes comment='salt minion registered'"
        fi
        if [ "x${registered}" = "x" ];then
            bs_log "Failed accepting mastersalt key on ${MASTERSALT} for ${minion_id}"
            warn_log
            exit 1
        fi
    fi
}

lazy_start_mastersalt_daemons() {
    if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
        if [ "x$(mastersalt_master_processes)" = "x0" ] || [ "x${mastersalt_master_changed}" = "x1" ];then
            restart_local_mastersalt_masters
            sleep 2
            if [ "x$(mastersalt_master_processes)" = "x0" ];then
                die "Masteralt Master start failed"
            fi
        fi
    fi
    if [ "x${IS_MASTERSALT_MINION}" != "x" ] || [ "${mastersalt_minion_changed}" = "x1" ] ;then
        if [ "x$(mastersalt_minion_processes)" = "x0" ];then
            restart_local_mastersalt_minions
            sleep 2
            if [ "x$(mastersalt_minion_processes)" = "x0" ];then
                die "Masteralt Minion start failed"
            fi
        fi
    fi
}

run_salt_bootstrap_() {
    salt_type=${1}
    bs=${2}
    bs_log "Running ${salt_type} bootstrap: ${bs}"
    ${salt_type}_call_wrapper --local state.sls ${bs}
    if [ "x${SALT_BOOT_DEBUG}" != "x" ];then cat "${SALT_BOOT_OUTFILE}";fi
    warn_log
    if [ "x${last_salt_retcode}" != "x0" ];then
        echo "${salt_type}: Failed bootstrap: ${bs}"
        exit 1
    fi
}

run_salt_bootstrap() {
    run_salt_bootstrap_ salt ${@}
}

run_mastersalt_bootstrap() {
    run_salt_bootstrap_ mastersalt ${@}
}


install_mastersalt_daemons() {
    # --------- check if we need to run mastersalt setup's
    RUN_MASTERSALT_BOOTSTRAP="${SALT_REBOOTSTRAP}"
    # regenerate keys if missings
    if [ $(which salt-key 2>/dev/null) ];then
        gen_mastersalt_keys
    fi
    if [ "x${IS_MASTERSALT}" != "x" ];then
        if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            if  [ ! -e "${MCONF_PREFIX}/pki/master/master.pem" ]\
                || [ ! -e "${MCONF_PREFIX}/master.d/00_global.conf" ];then
                RUN_MASTERSALT_BOOTSTRAP="1"
            fi
        fi
        if     [ ! -e "${MCONF_PREFIX}" ]\
            || [ ! -e "${MCONF_PREFIX}/minion.d/00_global.conf" ]\
            || [ ! -e "${MCONF_PREFIX}/pki/minion/minion.pem" ]\
            || [ -e "${MASTERSALT_MS}/.rebootstrap" ]\
            || [ "x$(grep makina-states.controllers.mastersalt_ "${MCONF_PREFIX}/grains" 2>/dev/null |wc -l|${SED} -e "s/ //g")" = "x0" ]\
            || [ ! -e "${BIN_DIR}/mastersalt" ]\
            || [ ! -e "${BIN_DIR}/mastersalt-master" ]\
            || [ ! -e "${BIN_DIR}/mastersalt-key" ]\
            || [ ! -e "${BIN_DIR}/mastersalt-ssh" ]\
            || [ ! -e "${BIN_DIR}/mastersalt-syndic" ]\
            || [ ! -e "${BIN_DIR}/mastersalt-cp" ]\
            || [ ! -e "${BIN_DIR}/mastersalt-minion" ]\
            || [ ! -e "${BIN_DIR}/mastersalt-call" ]\
            || [ ! -e "${BIN_DIR}/mastersalt" ]\
            || [ ! -e "${MCONF_PREFIX}/pki/minion/minion.pem" ];then
            if [ -e "${MASTERSALT_MS}/.rebootstrap" ];then
                rm -f "${MASTERSALT_MS}/.rebootstrap"
            fi
            RUN_MASTERSALT_BOOTSTRAP="1"
        fi
    fi
    if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
        if [ ! -e "${ETC_INIT}.d/mastersalt-master" ]\
            &&  [ ! -e "${ETC_INIT}/mastersalt-master.conf" ];then
            RUN_MASTERSALT_BOOTSTRAP="1"
        fi
    fi
    if  [ "x${IS_MASTERSALT_MINION}" != "x" ];then
        if [ ! -e "${ETC_INIT}.d/mastersalt-minion" ]\
            && [ ! -e "${ETC_INIT}/mastersalt-minion.conf" ];then
            RUN_MASTERSALT_BOOTSTRAP="1"
        fi
    fi
    if [  "${SALT_BOOT_DEBUG}" != "x" ];then
        debug_msg "mastersalt:"
        debug_msg "RUN_MASTERSALT_BOOTSTRAP: $RUN_MASTERSALT_BOOTSTRAP"
        debug_msg "grains: $(grep makina-states.controllers.mastersalt_ "${MCONF_PREFIX}/grains" |wc -l|${SED} -e "s/ //g")"
        debug_msg $(ls  "${BIN_DIR}/mastersalt-master" "${BIN_DIR}/mastersalt-key" \
            "${BIN_DIR}/mastersalt-minion" "${BIN_DIR}/mastersalt-call" \
            "${BIN_DIR}/mastersalt" "${MCONF_PREFIX}" \
            "${MCONF_PREFIX}/pki/minion/minion.pem" 1>/dev/null)
    fi

    # --------- MASTERSALT
    # in case of redoing a bootstrap for wiring on mastersalt
    # after having already bootstrapped using a regular salt
    # installation,
    # we will run the specific mastersalt parts to wire
    # on the global mastersalt
    if [ "x${RUN_MASTERSALT_BOOTSTRAP}" != "x" ];then
        ds=y
        # kill salt running daemons if any
        if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            killall_local_mastersalt_masters
        fi
        if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
            killall_local_mastersalt_minions
        fi

        # run mastersalt master+minion boot_nodetype bootstrap
        ${SED} -i -e "/makina-states.nodetypes.$(get_salt_nodetype):/ d"  "${MCONF_PREFIX}/grains"
        echo "makina-states.nodetypes.$(get_salt_nodetype): true" >> "${MCONF_PREFIX}/grains"
        run_mastersalt_bootstrap ${mastersalt_bootstrap_nodetype}

        # run mastersalt master setup
        if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            run_mastersalt_bootstrap ${mastersalt_bootstrap_master}
        fi

        if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
            # run mastersalt minion setup
            run_mastersalt_bootstrap ${mastersalt_bootstrap_minion}
        fi

        gen_mastersalt_keys

        # kill mastersalt running daemons if any
        # restart mastersalt salt-master after setup
        if [ "x$(get_local_mastersalt_mode)" = "xmasterless" ] && [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            debug_msg "Forcing mastersalt master restart"
            restart_local_mastersalt_masters
            sleep 10
        else
            debug_msg "Forcing mastersalt master shutdown"
            killall_local_mastersalt_masters
        fi
        if [ "x$(get_local_mastersalt_mode)" = "xmasterless" ] && [ "x${IS_MASTERSALT_MINION}" != "x" ];then
        # restart mastersalt minion
            debug_msg "Forcing mastersalt minion restart"
            restart_local_mastersalt_minions
        else
            debug_msg "Forcing mastersalt minion shutdown"
            killall_local_mastersalt_minions
        fi
        SALT_BOOT_NOW_INSTALLED="y"
    else
        if [ "x${QUIET}" = "x" ];then
            if [ "x${IS_MASTERSALT}" != "x" ];then
                bs_log "Skip MasterSalt installation, already done"
            fi
        fi
    fi
}

install_mastersalt_env() {
    if [ "x${IS_MASTERSALT}" = "x" ];then return;fi
    install_mastersalt_daemons
    lazy_start_mastersalt_daemons
    make_mastersalt_association
}

install_salt_env() {
    if [ "x${IS_SALT}" = "x" ];then return;fi
    # XXX: important mastersalt must be configured before salt
    # to override possible local settings.
    install_salt_daemons
    lazy_start_salt_daemons
    make_association
    # --------- stateful state return: mark as already installed
    if [ "x${ds}" = "x" ];then
        salt_echo 'changed=false comment="already bootstrapped"'
    fi
}

# --------- HIGH-STATES

highstate_in_mastersalt_env() {
    # IMPORTANT: MASTERSALT BEFORE SALT !!!
    if [ "x${SALT_BOOT_SKIP_HIGHSTATES}" = "x" ]\
        && [ "x${MASTERSALT_BOOT_SKIP_HIGHSTATE}" = "x" ];then
        bs_log "Running makina-states highstate for mastersalt"
        bs_log "    export MASTERSALT_BOOT_SKIP_HIGHSTATE=1 to skip (dangerous)"
        LOCAL=""
        if [ "x$(mastersalt_ping_test)" != "x0" ];then
            LOCAL="--local $LOCAL"
            bs_yellow_log " [bs] mastersalt highstate running offline !"
        fi
        mastersalt_call_wrapper $LOCAL state.highstate
        if [ "x${SALT_BOOT_DEBUG}" != "x" ];then cat "${SALT_BOOT_OUTFILE}";fi
        warn_log
        if [ "x${last_salt_retcode}" != "x0" ];then
            bs_log "Failed highstate for mastersalt"
            exit 1
        fi
        warn_log
        salt_echo "changed=yes comment='mastersalt highstate run'"
    else
        salt_echo "changed=false comment='mastersalt highstate skipped'"
    fi
}

highstate_in_salt_env() {
    if [ "x${SALT_BOOT_SKIP_HIGHSTATES}" = "x" ]\
        && [ "x${SALT_BOOT_SKIP_HIGHSTATE}" = "x" ];then
        bs_log "Running makina-states highstate"
        bs_log "    export SALT_BOOT_SKIP_HIGHSTATE=1 to skip (dangerous)"
        LOCAL=""
        if [ "x$(salt_ping_test)" != "x0" ];then
            bs_yellow_log " [bs] salt highstate running offline !"
            LOCAL="--local ${LOCAL}"
        fi
        salt_call_wrapper ${LOCAL} state.highstate
        if [ "x${last_salt_retcode}" != "x0" ];then
            bs_log "Failed highstate"
            warn_log
            exit 1
        fi
        warn_log
        salt_echo "changed=yes comment='salt highstate run'"
    else
        salt_echo "changed=false comment='salt highstate skipped'"
    fi
    if [ "x${SALT_BOOT_DEBUG}" != "x" ];then cat "$SALT_BOOT_OUTFILE";fi

    # --------- stateful state return: mark as freshly installed
    if [ "x${SALT_BOOT_NOW_INSTALLED}" != "x" ];then
        warn_log
        salt_echo "changed=yes comment='salt installed and configured'"
    fi

}

run_highstates() {
    if [ "x${IS_SALT}" != "x" ];then
        highstate_in_salt_env
    fi
    if [ "x${IS_MASTERSALT}" != "x" ];then
        highstate_in_mastersalt_env
    fi
}

cleanup_old_installs() {
    if [ -e "${SALT_MS}/.installed.cfg" ] || [ -e "${MASTERSALT_MS}/.installed.cfg" ];then
        upgrade_from_buildout
    fi
    #for conf in "${minion_conf}" "${mminion_conf}";do
    #    if [ -e "$conf" ];then
    #        if [ "x$(egrep "^grain_dirs:" "${conf}"|wc -l|${SED} -e "s/ //g")" = "x0" ];then
    #            bs_log "Patching grains_dirs -> grain_dirs in ${conf}"
    #            "${SED}" -i -e "s:grains_dirs:grain_dirs:g" "${conf}"
    #        fi
    #        for i in grains modules renderers returners states;do
    #            if [ "x$(grep "makina-states/mc_states/${i}" "${conf}"|wc -l|${SED} -e "s/ //g")" = "x0" ];then
    #                bs_log "Patching ext_mods/${i} to mc_states/${i} in $conf"
    #                new_path="makina-states/mc_states/${i}"
    #                "${SED}" -i -e "s:makina-states/_${i}:${new_path}:g" "$conf"
    #                "${SED}" -i -e "s:makina-states/_${i}/mc_${i}:${new_path}:g" "$conf"
    #                "${SED}" -i -e "s:makina-states/ext_mods/mc_states/${i}:${new_path}:g" "$conf"
    #                "${SED}" -i -e "s:makina-states/ext_mods/${i}:${new_path}:g" "$conf"
    #                "${SED}" -i -e "s:makina-states/ext_mods/mc_${i}:${new_path}:g" "$conf"
    #                "${SED}" -i -e "s:makina-states/mc_salt/mc_${i}:${new_path}:g" "$conf"
    #            fi
    #        done
    #    fi
    #done
    #ls \
    #    "${SALT_MS}/_states/mc_apache.py"* \
    #    2>/dev/null|while read oldmode;do
    #    rm -fv "${oldmode}"
    #done
    #ls -d \
    #    "${MASTERSALT_MS}/_modules/"    \
    #    2>/dev/null|while read oldmode;do
    #    rm -frv "${oldmode}"
    #done
    if [ "x$(egrep "bootstrapped\.salt" ${MCONF_PREFIX}/grains 2>/dev/null |wc -l|${SED} -e "s/ //g")" != "x0" ];then
        bs_log "Cleanup old mastersalt grains"
        "${SED}" -i -e "/bootstrap\.salt/d" "${MCONF_PREFIX}/grains"
        mastersalt_call_wrapper --local saltutil.sync_grains
    fi
    if [ "x$(grep mastersalt ${CONF_PREFIX}/grains 2>/dev/null |wc -l|${SED} -e "s/ //g")" != "x0" ];then
        bs_log "Cleanup old salt grains"
        "${SED}" -i -e "/mastersalt/d" "${CONF_PREFIX}/grains"
        salt_call_wrapper --local saltutil.sync_grains
    fi
}

bs_help() {
    title=${1}
    shift
    help=${1}
    shift
    default=${1}
    shift
    opt=${1}
    shift
    msg="     ${YELLOW}${title} ${NORMAL}${CYAN}${help}${NORMAL}"
    if [ "x${opt}" = "x" ];then
        msg="${msg} ${YELLOW}(mandatory)${NORMAL}"
    fi
    if [ "x${default}" != "x" ];then
        msg="${msg} ($default)"
    fi
    printf "${msg}\n"
}

exemple() {
    sname="./$(basename ${THIS})"
    printf "     ${YELLOW}${sname}${1} ${CYAN}${2}${NORMAL}\n"

}

usage() {
    set_colors
    bs_log "${THIS}:"
    echo
    bs_yellow_log "This script will install salt minion(s) and maybe master(s) on different flavors (salt/mastersalt) on top of makina-states"
    bs_yellow_log "This script installs by default a salt master/minion pair on localhost"
    bs_yellow_log "This script can also install a mastersalt minion and maybe a mastersalt master."
    bs_yellow_log "It will install first what the server needed as requirements and system settings, then the saltstate stuff"
    if [ "x${SALT_LONG_HELP}" != "x" ];then
        echo
        bs_yellow_log "You may need to select the nodetype, and the other informations bits neccesary to"
        bs_yellow_log "desccribe and adapt the behavior to your targeted environment"
        echo
        bs_log "Examples"
        exemple ":" "install a saltmaster/minion"
        exemple " --nodetype=devhost" "install a saltmaster/minion in 'development' mode"
        exemple " --mastersalt mastersalt.mycompany.net" "install a mastersalt minion linked to mastersalt.mycompany.net"
    fi
    echo
    bs_log "  General settings"
    bs_help "    -b|--branch <branch>" "MakinaStates branch to use" "${MS_BRANCH}" y
    bs_help "    -h|--help / -l/--long-help" "this help message or the long & detailed one" "" y
    bs_help "    -C|--no-confirm" "Do not ask for start confirmation" "" y
    bs_help "    -S|--skip-checkouts" "Skip initial checkouts / updates" "" y
    bs_help "    -s|--skip-highstates" "Skip highstates" "" y
    bs_help "    -d|--debug" "debug/verbose mode" "NOT SET" y
    bs_help "    --debug-level <level>" "debug level (quiet|all|info|error)" "NOT SET" y
    bs_help "    -n|--nodetype <nt>" "Nodetype to install into (devhost | server | dockercontainer | lxcontainer | vm | vagrantvm)" "$(get_salt_nodetype)" "y"
    bs_help "    -m|--minion-id" "Minion id" "$(get_minion_id)" y
    bs_help "    --no-colors" "No terminal colors" "${NO_COLORS}" "y"
    bs_log "  Actions (no action means install)"
    bs_help "    --upgrade" "Run bootsalt upgrade code (primarely destinated to run as the highstate wrapper to use in crons)" "" "${IS_SALT_UPGRADING}"
    bs_help "    --refresh-modules" "refresh salt & mastersalt modules, grains & pillar (refresh all)" "" "y"
    bs_help "    --synchronize-code" "Only sync sourcecode" "${SALT_BOOT_SYNC_CODE}" y
    bs_help "    --check-alive" "restart daemons if they are down" "" "y"
    bs_help "    --restart-daemons" "restart master & minions daemons" "" "y"
    bs_help "    --kill" "Kill all daemons" "${SALT_BOOT_CLEANUP}" y
    bs_help "    --cleanup" "Cleanup old execution logfiles" "${SALT_BOOT_CLEANUP}" y
    bs_help "    --restart-masters" "restart master daemons" "" "y"
    bs_help "    --restart-minions" "restart minion daemons" "" "y"
    bs_help "    --reattach" "Reattach a mastersalt minion ba${SED} install to a new master (saltcloud/config.seed) (need new key/confs via --reattach-dir)" "${SALT_REATTACH}" y
    if [ "x${SALT_LONG_HELP}" != "x" ];then
        bs_help "    --salt-rebootstrap" "Redo salt bootstrap" "${SALT_REBOOTSTRAP}" "y"
        bs_help "    --venv-rebootstrap" "Redo venv, salt bootstrap" "${VENV_REBOOTSTRAP}" "y"
    fi
    bs_log "  Actions settings"
    bs_help "    -g|--makina-states-url <url>" "makina-states url" "${MAKINASTATES_URL}" y
    bs_help "    --reattach-dir" "for --reattach, the directory to grab salt master/minion new keys & conf from" "${SALT_REATTACH_DIR}" y
    if [ "x${SALT_LONG_HELP}" != "x" ];then
        bs_help "    -r|--root <path>" "/ path" "${ROOT}"
        bs_help "    -p|--prefix <path>" "prefix path" "${PREFIX}" yi
    fi
    bs_log "  Switches"
    bs_help "    --no-mastersalt" "Do not install mastersalt daemons" "" y
    bs_help "    --no-salt" "Do not install salt daemons" "" y
    if [ "x${SALT_LONG_HELP}" != "x" ];then
        bs_help "    -M|--salt-master" "install a salt master" "${IS_SALT_MASTER}" y
        bs_help "    -N|--salt-minion" "install a salt minion" "${IS_SALT_MINION}" y
        bs_help "    -no-M|--no-salt-master" "Do not install a salt master" "${IS_SALT_MASTER}" y
        bs_help "    -no-N|--no-salt-minion" "Do not install a salt minion" "${IS_SALT_MINION}" y
        bs_help "    -NN|--mastersalt-minion" "install a mastersalt minion" "${IS_MASTERSALT_MINION}" y
        bs_help "    -MM|--mastersalt-master" "install a mastersalt master" "${IS_MASTERSALT_MASTER}" y
        bs_help "    -no-MM|--no-mastersalt-master" "do not install a mastersalt master" "${IS_MASTERSALT_MASTER}" y
        bs_help "    -no-NN|--no-mastersalt-minion" "do not install a mastersalt minion" "${IS_MASTERSALT_MINION}" y
    fi
    bs_log "  Salt settings"
    bs_help "    --local-salt-mode" "Do we run masterless salt (masterless/remote)" "$(get_local_salt_mode)" y
    bs_help "    --salt-master-dns <hostname>" "DNS of the salt master" "${SALT_MASTER_DNS}" y
    bs_help "    --salt-master-port <port>"        "Port of the salt master" "${MASTERSALT_MASTER_PORT}" y
    if [ "x${SALT_LONG_HELP}" != "x" ];then
        bs_help "    --salt-master-ip <ip>"  "IP of the salt master" "${SALT_MASTER_IP}" y
        bs_help "    --salt-master-publish-port" "Salt master publish port" "${SALT_MASTER_PUBLISH_PORT}" y
        bs_help "    --salt-minion-dns <dns>" "DNS of the salt minion" "${SALT_MINION_DNS}" "y"
    fi
    bs_log "  Mastersalt settings (if any)"
    printf "    ${YELLOW}   by default, we only install a minion, unless you add -MM${NORMAL}\n"
    bs_help "    --local-mastersalt-mode" "Do we run masterless mastersalt (masterless/remote)" "$(get_local_mastersalt_mode)" y
    bs_help "    --mastersalt <dns>" "DNS of the mastersalt master" "${MASTERSALT_MASTER_DNS}" y
    bs_help "    --mastersalt-master-port <port>"  "Port of the mastersalt master" "${MASTERSALT_MASTER_PORT}" y
    if [ "x${SALT_LONG_HELP}" != "x" ];then
        bs_help "    --mastersalt-master-ip <ip>"  "IP of the mastersalt master" "${MASTERSALT_MASTER_IP}" y
        bs_help "    --mastersalt-master-publish-port <port>" "MasterSalt master publish port" "${MASTERSALT_MASTER_PUBLISH_PORT}" y
        bs_help "    --mastersalt-minion-dns <dns>"  "DNS of the mastersalt minion" "${MASTERSALT_MINION_DNS}" y
    fi
}

parse_cli_opts() {
    #set_vars # to collect defaults for the help message
    args="${@}"
    PARAM=""
    while true
    do
        sh=1
        argmatch=""
        if [ "x${1}" = "x${PARAM}" ];then
            break
        fi
        if [ "x${1}" = "x--from-salt-cloud" ] || [ "x${1}" = "x--reattach" ];then
            SALT_REATTACH="1"
            argmatch="1"
        fi
        if [ "x${1}" = "x--salt-cloud-dir" ] || [ "x${1}" = "x--reattach-dir" ] ;then
            SALT_REATTACH_DIR="$2";sh="2";argmatch="1"
            SALT_REATTACH="1"
            SALT_BOOT_SKIP_HIGHSTATES="1"
        fi
        if [ "x${SALT_REATTACH}" != "x" ];then
            # will read /tmp/.<>/minion's master's value
            IS_MASTERSALT="yes"
            SALT_BOOT_SKIP_HIGHSTATES="1"
            FORCE_IS_MASTERSALT="yes"
            FORCE_IS_MASTERSALT_MINION="yes"
        fi
        if [ "x${1}" = "x-q" ] || [ "x${1}" = "x--quiet" ];then
            QUIET="1";argmatch="1"
        fi
        if [ "x${1}" = "x-h" ] || [ "x${1}" = "x--help" ];then
            USAGE="1";argmatch="1"
        fi
        if [ "x${1}" = "x-l" ] || [ "x${1}" = "x--long-help" ];then
            SALT_LONG_HELP="1";USAGE="1";argmatch="1"
        fi
        if [ "x${1}" = "x-d" ] || [ "x${1}" = "x--debug" ];then
            SALT_BOOT_DEBUG="y";argmatch="1"
        fi
        if [ "x${1}" = "x--debug-level" ];then
            SALT_BOOT_DEBUG_LEVEL="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--no-colors" ];then
            NO_COLORS="1";argmatch="1"
        fi
        if [ "x${1}" = "x--upgrade" ];then
            IS_SALT_UPGRADING="1";argmatch="1"
        fi
        if [ "x${1}" = "x--cleanup" ];then
            SALT_BOOT_CLEANUP="1";argmatch="1"
        fi
        if [ "x${1}" = "x--salt-rebootstrap" ];then
            SALT_REBOOTSTRAP="1";argmatch="1"
        fi
        if [ "x${1}" = "x-S" ] || [ "x${1}" = "x--skip-checkouts" ];then
            SALT_BOOT_SKIP_CHECKOUTS="y";argmatch="1"
        fi
        if [ "x${1}" = "x-s" ] || [ "x${1}" = "x--skip-highstates" ];then
            SALT_BOOT_SKIP_HIGHSTATES=y;argmatch="1"
        fi
        if [ "x${1}" = "x-C" ] || [ "x${1}" = "x--no-confirm" ];then
            SALT_BOOT_NOCONFIRM="y";argmatch="1"
        fi
        if [ "x${1}" = "x-M" ] || [ "x${1}" = "x--salt-master" ];then
            IS_SALT_MASTER="y";argmatch="1"
        fi
        if [ "x${1}" = "x-N" ] || [ "x${1}" = "x--salt-minion" ];then
            IS_SALT_MINION="y";argmatch="1"
        fi
        if [ "x${1}" = "x--kill" ];then
            SALT_BOOT_KILL="1"
            argmatch="1"
        fi
        if [ "x${1}" = "x--check-alive" ];then
            SALT_BOOT_LIGHT_VARS="1"
            SALT_BOOT_SKIP_HIGHSTATES="1"
            SALT_BOOT_SKIP_CHECKOUTS="1"
            SALT_BOOT_CHECK_ALIVE="y"
            argmatch="1"
        fi
        if [ "x${1}" = "x--restart-masters" ];then
            SALT_BOOT_LIGHT_VARS="1"
            SALT_BOOT_SKIP_HIGHSTATES="1"
            SALT_BOOT_SKIP_CHECKOUTS="1"
            SALT_BOOT_CHECK_ALIVE="y"
            SALT_BOOT_RESTART_MASTERS="y";argmatch="1"
        fi
        if [ "x${1}" = "x--restart-minions" ];then
            SALT_BOOT_LIGHT_VARS="1"
            SALT_BOOT_SKIP_HIGHSTATES="1"
            SALT_BOOT_SKIP_CHECKOUTS="1"
            SALT_BOOT_CHECK_ALIVE="y"
            SALT_BOOT_RESTART_MINIONS="y";argmatch="1"
        fi
        if [ "x${1}" = "x--refresh-modules" ];then
            SALT_BOOT_LIGHT_VARS="1"
            DO_REFRESH_MODULES=1
            SALT_BOOT_SKIP_HIGHSTATES="1"
            SALT_BOOT_SKIP_CHECKOUTS=""
            argmatch="1"
        fi
        if [ "x${1}" = "x--initial-highstate" ];then
            SALT_BOOT_LIGHT_VARS="1"
            SALT_BOOT_NOCONFIRM="1"
            BUILDOUT_REBOOTSTRAP="1"
            SALT_BOOT_INITIAL_HIGHSTATE="1"
            SALT_BOOT_SKIP_HIGHSTATES=""
            SALT_BOOT_SKIP_CHECKOUTS="1"
            argmatch="1"
        fi
        if [ "x${1}" = "x--synchronize-code" ];then
            SALT_BOOT_LIGHT_VARS="1"
            SALT_BOOT_SYNC_CODE="1"
            SALT_BOOT_SKIP_HIGHSTATES="1"
            SALT_BOOT_SKIP_CHECKOUTS=""
            argmatch="1"
        fi
        if [ "x${1}" = "x--restart-daemons" ];then
            SALT_BOOT_LIGHT_VARS="1"
            SALT_BOOT_SKIP_HIGHSTATES="1"
            SALT_BOOT_SKIP_CHECKOUTS="1"
            SALT_BOOT_CHECK_ALIVE="y"
            SALT_BOOT_RESTART_DAEMONS="y"
            argmatch="1"
        fi
        if [ "x${1}" = "x-MM" ] || [ "x${1}" = "x--mastersalt-master" ];then
            FORCE_IS_MASTERSALT_MASTER="yes"
            IS_MASTERSALT_MASTER="y"
            argmatch="1"
        fi
        if [ "x${1}" = "x-NN" ] || [ "x${1}" = "x--mastersalt-minion" ];then
            FORCE_IS_MASTERSALT_MINION="yes"
            IS_MASTERSALT_MINION="y"
            argmatch="1"
        fi
        if [ "x${1}" = "x--local-salt-mode" ];then
            FORCE_LOCAL_SALT_MODE="${2}"; sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--local-mastersalt-mode" ];then
            FORCE_LOCAL_MASTERSALT_MODE="${2}"; sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-no-M" ] || [ "x${1}" = "x--no-salt-master" ];then
            FORCE_IS_SALT_MASTER="no"
            IS_SALT_MASTER=""
            argmatch="1"
        fi
        if [ "x${1}" = "x-no-N" ] || [ "x${1}" = "x--no-salt-minion" ];then
            FORCE_IS_SALT_MINION="no"
            IS_SALT_MINION=""
            argmatch="1"
        fi
        if [ "x${1}" = "x--no-salt" ];then
            FORCE_IS_SALT="no"
            FORCE_IS_SALT_MINION="no"
            FORCE_IS_SALT_MASTER="no"
            IS_SALT=""
            IS_SALT_MINION=""
            IS_SALT_MASTER=""
            argmatch="1"
        fi
        if [ "x${1}" = "x-no-MM" ] || [ "x${1}" = "x--no-mastersalt-master" ];then
            FORCE_IS_MASTERSALT_MASTER="no"
            IS_MASTERSALT_MASTER=""
            argmatch="1"
        fi
        if [ "x${1}" = "x-no-NN" ] || [ "x${1}" = "x--no-mastersalt-minion" ];then
            FORCE_IS_MASTERSALT_MINION="no"
            IS_MASTERSALT_MINION=""
            argmatch="1"
        fi
        if [ "x${1}" = "x--no-mastersalt" ];then
            FORCE_IS_MASTERSALT="no"
            IS_MASTERSALT=""
            FORCE_IS_MASTERSALT_MASTER="no"
            IS_MASTERSALT_MASTER=""
            FORCE_IS_MASTERSALT_MINION="no"
            IS_MASTERSALT_MINION=""
            argmatch="1"
        fi
        if [ "x${1}" = "x-m" ] || [ "x${1}" = "x--minion-id" ];then
            FORCE_SALT_MINION_ID=1;FORCE_MASTERSALT_MINION_ID=1;SALT_MINION_ID="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--mastersalt-minion-id" ];then
            FORCE_MASTERSALT_MINION_ID=1;MASTERSALT_MINION_ID="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-mac" ] || [ "x${1}" = "x--master-controller" ];then
            SALT_MASTER_CONTROLLER="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-mmac" ] || [ "x${1}" = "x--mastersalt-master-controller" ];then
            MASTERSALT_MASTER_CONTROLLER="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-mic" ] || [ "x${1}" = "x--minion-controller" ];then
            SALT_MINION_CONTROLLER="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-mmic" ] || [ "x${1}" = "x--mastersalt-minion-controller" ];then
            MASTERSALT_MINION_CONTROLLER="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--salt-master-dns" ];then
            SALT_MASTER_DNS="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--salt-master-ip" ];then
            SALT_MASTER_IP="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--mastersalt-master-ip" ];then
            MASTERSALT_MASTER_IP="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--salt-minion-dns" ];then
            SALT_MINION_DNS="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--mastersalt-minion-dns" ];then
            MASTERSALT_MINION_DNS="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--salt-master-port" ];then
            SALT_MASTER_PORT="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--salt-master-publish-port" ];then
            SALT_MASTER_PUBLISH_PORT="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--mastersalt-master-port" ];then
            MASTERSALT_MASTER_PORT="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--mastersalt-master-publish-port" ];then
            MASTERSALT_MASTER_PUBLISH_PORT="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-n" ] || [ "x${1}" = "x--nodetype" ];then
            FORCE_SALT_NODETYPE="1"; SALT_NODETYPE="${2}"; sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-g" ] || [ "x${1}" = "x--makina-states-url" ];then
            MAKINASTATES_URL="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--mastersalt" ];then
            MASTERSALT="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-p" ] || [ "x${1}" = "x--prefix" ];then
            PREFIX="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-b" ] || [ "x${1}" = "x--branch" ];then
            FORCE_MS_BRANCH=1;MS_BRANCH="${2}";sh="2";argmatch="1"
        fi
        if [ "x${argmatch}" != "x1" ];then
            USAGE="1"
            break
        fi
        PARAM="${1}"
        OLD_ARG="${1}"
        for i in $(seq $sh);do
            shift
            if [ "x${1}" = "x${OLD_ARG}" ];then
                break
            fi
        done
        if [ "x${1}" = "x" ];then
            break
        fi
    done
    if [ "x${USAGE}" != "x" ];then
        usage
        exit 0
    fi
}

restart_daemons() {
    cleanup_old_installs
    if [ "x${IS_SALT_MINION}" != "x" ];then
        restart_local_minions
    fi
    if [ "x${IS_SALT_MASTER}" != "x" ];then
        restart_local_masters
    fi
    if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
        restart_local_mastersalt_masters
    fi
    if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
        restart_local_mastersalt_minions
    fi
}

ps_etime() {
    ${PS} -eo pid,comm,etime,args | perl -ane '@t=reverse(split(/[:-]/, $F[2])); $s=$t[0]+$t[1]*60+$t[2]*3600+$t[3]*86400;$cmd=join(" ", @F[3..$#F]);print "$F[0]\t$s\t$F[1]\t$F[2]\t$cmd\n"'
}

start_missing_or_dead() {
    if [ "x$(get_local_salt_mode)" != "xmasterless" ]\
        && [ "x${IS_SALT_MASTER}" != "x" ]\
        && [ "x$(master_processes)" = "x0" ];then
        if [ "x${QUIET}" = "x" ];then
            bs_log "Zero master, restarting them all"
        fi
        killall_local_masters
        restart_local_masters
    fi
    if [ "x${IS_MASTERSALT_MASTER}" != "x" ] && [ "x$(mastersalt_master_processes)" = "x0" ];then
        if [ "x${QUIET}" = "x" ];then
            bs_log "Zero mastersalt master, restarting them all"
        fi
        killall_local_mastersalt_masters
        restart_local_mastersalt_masters
    fi
    if [ "x$(get_local_salt_mode)" != "xmasterless" ]\
        && [ "x${IS_SALT_MINION}" != "x" ]\
        && [ "x$(minion_processes)" != "x2" ];then
        if [ "x${QUIET}" = "x" ];then
            bs_log "More than one or zero minion, restarting them all"
        fi
        killall_local_minions
        restart_local_minions
    fi
    if [ "x${IS_MASTERSALT_MINION}" != "x" ] && [ "x$(mastersalt_minion_processes)" != "x2" ];then
        if [ "x${QUIET}" = "x" ];then
            bs_log "More than one or zero mastersalt minion, restarting them all"
        fi
        killall_local_mastersalt_minions
        restart_local_mastersalt_minions
    fi
}

check_alive() {
    if [ -e "${ALIVE_MARKER}" ];then
        return
    fi
    restart_modes=""
    kill_old_syncs
    # kill all check alive
    ps_etime|sort -n -k2|egrep "boot-salt.*alive"|grep -v grep|while read psline;
    do
        seconds="$(echo "$psline"|awk '{print $2}')"
        pid="$(filter_host_pids $(echo $psline|awk '{print $1}'))"
        if [ "x${pid}" != "x" ] && [ "${seconds}" -gt "300" ];then
            bs_log "something was wrong with last restart, killing old check alive process: $pid"
            bs_log "${psline}"
            kill -9 "${pid}"
            killall_local_masters
            killall_local_minions
            killall_local_mastersalt_minions
            killall_local_mastersalt_minions
        fi
    done
    # kill all old (master)salt call (> 12 hours)
    ps_etime|sort -n -k2|egrep "salt-call"|grep mastersalt|grep -v grep|while read psline;
    do
        seconds="$(echo "$psline"|awk '{print $2}')"
        pid="$(filter_host_pids $(echo $psline|awk '{print $1}'))"
        if [ "x${pid}" != "x" ] && [ "${seconds}" -gt "$((60*60*12))" ];then
            bs_log "Something went wrong with last restart(mastersalt), killing old salt call process: $pid"
            bs_log "$psline"
            killall_local_mastersalt_masters
            killall_local_mastersalt_minions
        fi
    done
    ps_etime|sort -n -k2|egrep "salt-call"|grep -v mastersalt|grep -v grep|while read psline;
    do
        seconds="$(echo "$psline"|awk '{print $2}')"
        pid="$(filter_host_pids $(echo $psline|awk '{print $1}'))"
        if [ "x${pid}" != "x" ] && [ "${seconds}" -gt "$((60*60*12))" ];then
            bs_log "Something went wrong with last restart(salt), killing old salt call process: $pid"
            bs_log "$psline"
            killall_local_masters
            killall_local_minions
        fi
    done
    # kill all old (master)salt ping call (> 120 sec)
    ps_etime|sort -n -k2|egrep "salt-call"|grep test.ping|grep mastersalt|grep -v grep|while read psline;
    do
        seconds="$(echo "$psline"|awk '{print $2}')"
        pid="$(filter_host_pids $(echo $psline|awk '{print $1}'))"
        if [ "x${pid}" != "x" ] && [ "${seconds}" -gt "$((60*2))" ];then
            bs_log "MasterSalt PING stalled, killing old salt call process: $pid"
            bs_log "$psline"
            kill -9 "${pid}"
            killall_local_mastersalt_masters
            killall_local_mastersalt_minions
        fi
    done
    ps_etime|sort -n -k2|egrep "salt-call"|grep test.ping|grep -v mastersalt|grep -v grep|while read psline;
    do
        seconds="$(echo "$psline"|awk '{print $2}')"
        pid="$(filter_host_pids $(echo $psline|awk '{print $1}'))"
        if [ "x${pid}" != "x" ] && [ "${seconds}" -gt "$((60*2))" ];then
            bs_log "Salt PING stalled, killing old salt call process: $pid"
            bs_log "$psline"
            kill -9 "${pid}"
            killall_local_masters
            killall_local_minions
        fi
    done
    start_missing_or_dead
    # ping masters if we are not already forcing restart
    if [ "x${alive_mode}" != "xrestart" ];then
        if [ "x${IS_SALT}" != "x" ];then
            resultping="$(salt_ping_test)"
            if [ "x${resultping}" != "x0" ];then
                if [ "x${IS_SALT_MASTER}" != "x" ];then
                    killall_local_masters
                fi
                killall_local_minions
            fi
        fi
        if [ "x${IS_MASTERSALT}" != "x" ];then
            resultping="$(mastersalt_ping_test)"
            if [ "x${resultping}" != "x0" ];then
                if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
                    killall_local_mastersalt_masters
                fi
                killall_local_mastersalt_minions
            fi
        fi
    fi
    # last chance
    start_missing_or_dead
}

kill_old_syncs() {
    # kill all stale synchronnise code jobs
    ps_etime|sort -n -k2|egrep "boot-salt.*(synchronize-code|refresh-modules)"|grep -v grep|while read psline;
    do
        seconds="$(echo "$psline"|awk '{print $2}')"
        pid="$(filter_host_pids $(echo $psline|awk '{print $1}'))"
        # 8 minutes
        if [ "x${pid}" != "x" ] && [ "${seconds}" -gt "480" ];then
            bs_log "Something was wrong with last sync, killing old sync processes: $pid"
            bs_log "${psline}"
            kill -9 "${pid}"
        fi
    done
}

upgrade_from_buildout() {
    # upgrade from old buildout ba${SED} install
    s_venv=""
    if [ ! -e "${SALT_VENV_PATH}/bin/salt-call" ];then
        s_venv="1"
    fi
    if [ "x${IS_MASTERSALT}" != "x" ] && [ ! -e "${MASTERSALT_VENV_PATH}/bin/salt-call" ];then
        s_venv="1"
    fi
    if [ "x${s_venv}" != "x" ];then
        setup_virtualenvs
    fi
}

synchronize_code() {
    cleanup_old_installs
    restart_modes=""
    kill_old_syncs
    setup_and_maybe_update_code onlysync
    exit_status=0
    if [ "x${QUIET}" = "x" ];then
        bs_log "Code updated"
    fi
    if [ "x${1}" != "xno_refresh" ];then
        if [ "x${IS_SALT_MINION}" != "x" ] && [ "x$(get_local_salt_mode)" = "xremote" ];then
            salt_call_wrapper saltutil.sync_all
            if [ "x${last_salt_retcode}" != "x0" ];then
                bs_log "refreshed salt modules but there was a problem"
                exit_status=1
            else
                if [ "x${QUIET}" = "x" ];then
                    bs_log "refreshed salt modules"
                fi
            fi
        fi
        if [ "x${IS_MASTERSALT}" != "x" ] && [ "x$(get_local_mastersalt_mode)" = "xremote" ];then
            mastersalt_call_wrapper saltutil.sync_all
            if [ "x${last_salt_retcode}" != "x0" ];then
                bs_log "refreshed mastersalt modules but there was a problem"
                exit_status=1
            else
                if [ "x${QUIET}" = "x" ];then
                    bs_log "refreshed mastersalt modules"
                fi
            fi
        fi
    fi
    if [ "x${SALT_BOOT_INITIAL_HIGHSTATE}" = "x" ];then
        exit ${exit_status}
    fi
}

set_dns() {
    if [ "${NICKNAME_FQDN}" != "x" ];then
        if [ "x$(cat /etc/hostname 2>/dev/null|${SED} -e "s/ //")" != "x$(echo "${HOST}"|${SED} -e "s/ //g")" ]\
            && [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then
            bs_log "Resetting hostname file to ${HOST}"
            echo "${HOST}" > /etc/hostname

        fi
        for prefix in "${MCONF_PREFIX}" "${CONF_PREFIX}";do
            if [ "x$(cat "${prefix}/minion_id" 2>/dev/null|${SED} -e "s/ //")" != "x$(echo "${HOST}"|${SED} -e "s/ //g")" ];then
                if [ ! -d "${prefix}" ];then
                    mkdir -p "${prefix}"
                fi
                echo "${HOST}" > "${prefix}"/minion_id
            fi
        done
        if [ -e "$(which domainname 2>/dev/null)" ]\
            && [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then
            if [ "x$(domainname)" != "x$(echo "${DOMAINNAME}"|${SED} -e "s/ //g")" ];then
                bs_log "Resetting domainname to ${DOMAINNAME}"
                domainname "${DOMAINNAME}"
            fi
        fi
        if [ "x$(hostname)" != "x$(echo "${NICKNAME_FQDN}"|${SED} -e "s/ //g")" ]\
            && [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then
            bs_log "Resetting hostname to ${NICKNAME_FQDN}"
            hostname "${NICKNAME_FQDN}"
        fi
        if [ "x$(egrep -q "127.*${NICKNAME_FQDN}" /etc/hosts;echo ${?})" != "x0" ]\
            && [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then
            bs_log "Adding new core hostname alias to localhost"
            echo "127.0.0.1 ${NICKNAME_FQDN}">/tmp/hosts
            cat /etc/hosts>>/tmp/hosts
            echo "127.0.0.1 ${NICKNAME_FQDN}">>/tmp/hosts
            if [ -f /tmp/hosts ];then
                cp -f /tmp/hosts /etc/hosts
            fi
        fi
    fi
}

initial_highstates() {
    ret=${?}
    if [ "x$(get_conf initial_highstate)" != "x1" ];then
        run_highstates
        ret="${?}"
        # on failure try to sync code
        if [ "x${ret}" != "x0" ];then
            SALT_BOOT_SKIP_CHECKOUTS=""
            synchronize_code && run_highstates
            ret="${?}"
        fi
        if [ "x${ret}" = "x0" ];then
            set_conf initial_highstate 1
        fi
    fi
    exit ${ret}
}

cleanup_execlogs() {
    cleanup_old_installs
    LOG_LIMIT="${LOG_LIMIT:-20}"
    # keep 20 local exec logs only
    for dir in "${SALT_MS}/.bootlogs" "${MASTERSALT_MS}/.bootlogs";do
        if [ -e "${dir}" ];then
            cd "${dir}"
            if [ "$(ls -1|wc -l|${SED} -e "s/ //")" -gt "${LOG_LIMIT}" ];then
                ls -1rt|head -n $((-1*(${LOG_LIMIT}-$(ls -rt1|wc -l))))|while read fic;\
                do
                    opts="-f"
                    if [ "x${QUIET}" = "x" ];then
                        opts="${opts} -v"
                    fi
                    rm ${opts} "${fic}"
                done
            fi
        fi
    done
}

disable_service() {
    i="${1}"
    if [ -e "/etc/init/${i}.conf" ];then
        echo "manual" > "/etc/init/${i}.override"
    elif [  -e /etc/init.d/${i} ] && [ "x$(which update-rc.d 2>/dev/null)" != "x" ];then
        update-rc.d -f "${i}" remove
    fi
}

enable_service() {
    i="${1}"
    if [ -e "/etc/init/${i}.override" ];then
        rm -f "/etc/init/${i}.override"
    elif [  -e /etc/init.d/${i} ] && [ "x$(which update-rc.d 2>/dev/null)" != "x" ];then
        update-rc.d -f "${i}" defaults 99
    fi
}

stop_and_disable_service() {
    i="${1}"
    service_ "${i}" stop
    disable_service "${i}"
}

postinstall() {
   if [ "x${FORCE_IS_MASTERSALT_MASTER}" = "xno" ];then
         stop_and_disable_service mastersalt-master
         killall_local_mastersalt_masters
    fi
    if [ "x${FORCE_IS_SALT_MASTER}" = "xno" ];then
         stop_and_disable_service salt-master
         killall_local_masters
    fi
    if [ "x${SALT_REATTACH}" != "x" ];then
        lazy_start_mastersalt_daemons
    fi
}


if [ "x${SALT_BOOT_AS_FUNCS}" = "x" ];then
    detect_os
    set_progs
    parse_cli_opts $LAUNCH_ARGS
    set_vars # real variable affectation
    if [ "x$(dns_resolve localhost)" = "x${DNS_RESOLUTION_FAILED}" ];then
        die "${DNS_RESOLUTION_FAILED}"
    fi
    abort=""
    if [ "x${SALT_BOOT_KILL}" != "x" ];then
        kill_ms_daemons
        abort="1"
    fi
    if [ "x${SALT_BOOT_CLEANUP}" != "x" ];then
        cleanup_execlogs
        abort="1"
    fi
    if [ "x${SALT_BOOT_CHECK_ALIVE}" != "x" ];then
        check_alive
        abort="1"
    fi
    if [ "x${SALT_BOOT_INITIAL_HIGHSTATE}" != "x" ] \
        && [ x"$(get_conf initial_highstate)" = "x1" ];then
        exit 0
    fi
    if [ "x${SALT_BOOT_SYNC_CODE}" != "x" ];then
        synchronize_code no_refresh
    fi
    if [ "x${DO_REFRESH_MODULES}" != "x" ];then
        synchronize_code
    fi
    cleanup_old_installs
    if [ "x${SALT_BOOT_RESTART_MINIONS}" != "x" ];then
        restart_local_minions
        restart_local_mastersalt_minions
        abort="1"
    fi
    if [ "x${SALT_BOOT_RESTART_MASTERS}" != "x" ];then
        restart_local_masters
        restart_local_mastersalt_masters
        abort="1"
    fi
    if [ "x${SALT_BOOT_RESTART_DAEMONS}" != "x" ];then
        restart_daemons
        abort="1"
    fi
    if [ "x${abort}" = "x" ];then
        recap
        set_dns
        setup_and_maybe_update_code
        setup_virtualenvs
        create_salt_skeleton
        install_mastersalt_env
        install_salt_env
        if [ "x${SALT_BOOT_INITIAL_HIGHSTATE}" != "x" ];then
            initial_highstates
        else
            run_highstates
        fi
        # deprecated for a long time
        postinstall
    fi
    exit 0
fi
## vim:set et sts=5 ts=4 tw=0:

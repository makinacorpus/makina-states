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


# be sure to have a populated base path
PATH="${PATH}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"
export PATH

THIS="${0}"
VALID_BRANCHES=""
if [ -h "${THIS}" ];then
    THIS="$(readlink ${THIS})"
fi

LAUNCH_ARGS=${@}
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

RED="\\e[0;31m"
CYAN="\\e[0;36m"
YELLOW="\\e[0;33m"
NORMAL="\\e[0;0m"

SALT_BOOT_DEBUG="${SALT_BOOT_DEBUG:-}"
SALT_BOOT_DEBUG_LEVEL="${SALT_BOOT_DEBUG_LEVEL:-all}"
THIS="$(get_abspath ${THIS})"
DNS_RESOLUTION_FAILED="dns resolution failed"

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
    PYTHON="$(which python 2>/dev/null)"
    HOST="$(which host 2>/dev/null)"
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

ERROR_MSG="There were errors"


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
    printf "${CYAN}${@}${NORMAL}\n" 1>&2
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
    set_progs
    resolvers="hostsv4 hostsv6"
    for i in\
        "${GETENT}"\
        "${PERL}"\
        "${PYTHON}"\
        "${HOST}"\
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
    set_progs
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
            BEFORE_SAUCY=y
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
    if [ "x${IS_UBUNTU}" != "x" ];then
        SALT_BOOT_OS="ubuntu"
        DISTRIB_NEXT_RELEASE="saucy"
        DISTRIB_BACKPORT="${DISTRIB_NEXT_RELEASE}"
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
    if [ "x${SALT_CLOUD}" = "x" ];then
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


set_colors() {
    if [ "x${NO_COLORS}" != "x" ];then
        YELLOW=""
        RED=""
        CYAN=""
        NORMAL=""
    fi
}

get_minion_id_() {
    confdir="${1}"
    force="${3}"
    notfound=""
    if [ "x$(egrep -q "^id: [^ ]+" /etc/hosts $(find "${confdir}/minion"* -type f 2>/dev/null) 2>/dev/null;echo ${?})" != "x0" ]\
       || [ "$(find ${confdir}/minion* -type f 2>/dev/null|wc -l|sed -e "s/ //g")" ];then
       notfound="y"
    fi
    if [ "x${notfound}" != "x" ] && [ "x${SALT_CLOUD}" != "x" ] && [ -e "${SALT_CLOUD_DIR}/minion" ];then
        mmid="$(egrep "^id:" "${SALT_CLOUD_DIR}/minion"|awk '{print $2}'|sed -e "s/ //")"
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
    fi
    echo $mmid
}

mastersalt_get_minion_id() {
    get_minion_id_ "${MCONF_PREFIX}" "${MASTERSALT_MINION_ID}" "$FORCE_MASTERSALT_MINION_ID"
}


get_minion_id() {
    get_minion_id_ "$CONF_PREFIX" "$SALT_MINION_ID" "$FORCE_SALT_MINION_ID"
}

set_valid_upstreams() {
    if [ ! -e "$(which git 2>/dev/null)" ];then
        VALID_BRANCHES="master stable"
    fi
    if [ "x${VALID_BRANCHES}" = "x" ];then
        if [ "x${SALT_BOOT_LIGHT_VARS}" = "x" ];then
            VALID_BRANCHES="$(echo "$(git ls-remote "${STATES_URL}"|grep "refs/heads"|awk -F/ '{print $3}'|grep -v HEAD)")"
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

get_conf(){
    key="${1}"
    echo $(cat "${CONF_ROOT}/makina-states/$key" 2>/dev/null)
}

store_conf(){
    key="${1}"
    val="${2}"
    if [ ! -d "${CONF_ROOT}/makina-states" ];then
        mkdir -pv "${CONF_ROOT}/makina-states"
    fi
    echo "${val}">"${CONF_ROOT}/makina-states/${key}"
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
    if [ "x$(echo "${LAUNCH_ARGS}" | grep -q from-salt-cloud;echo ${?})" = "x0" ];then
        SALT_CLOUD="1"
    else
        SALT_CLOUD="${SALT_CLOUD:-}"
    fi
    SALT_CLOUD_DIR="${SALT_CLOUD_DIR:-"/tmp/.saltcloud"}"
    SALT_BOOT_LOCK_FILE="/tmp/boot_salt_sleep"
    LAST_RETCODE_FILE="/tmp/boot_salt_rc"
    QUIET=${QUIET:-}
    ROOT="${ROOT:-"/"}"
    CONF_ROOT="${CONF_ROOT:-"${ROOT}etc"}"
    ETC_INIT="${ETC_INIT:-"${CONF_ROOT}/init"}"
    detect_os
    set_progs
    CHRONO="$(get_chrono)"
    TRAVIS_DEBUG="${TRAVIS_DEBUG:-}"
    VENV_REBOOTSTRAP="${VENV_REBOOTSTRAP:-}"
    BUILDOUT_REBOOTSTRAP="${BUILDOUT_REBOOTSTRAP:-${VENV_REBOOTSTRAP}}"
    SALT_REBOOTSTRAP="${SALT_REBOOTSTRAP:-${VENV_REBOOTSTRAP}}"
    BASE_PACKAGES=""
    BASE_PACKAGES="$BASE_PACKAGES build-essential m4 libtool pkg-config autoconf gettext bzip2"
    BASE_PACKAGES="$BASE_PACKAGES groff man-db automake libsigc++-2.0-dev tcl8.5 python-dev"
    BASE_PACKAGES="$BASE_PACKAGES swig libssl-dev libyaml-dev debconf-utils python-virtualenv"
    BASE_PACKAGES="$BASE_PACKAGES vim git rsync"
    BASE_PACKAGES="$BASE_PACKAGES libzmq3-dev"
    BASE_PACKAGES="$BASE_PACKAGES libgmp3-dev"
    BRANCH_PILLAR_ID="makina-states.salt.makina-states.rev"
    MAKINASTATES_TEST=${MAKINASTATES_TEST:-}
    IS_SALT_UPGRADING="${IS_SALT_UPGRADING:-}"
    IS_SALT="${IS_SALT:-y}"
    IS_SALT_MASTER="${IS_SALT_MASTER:-y}"
    IS_SALT_MINION="${IS_SALT_MINION:-y}"
    IS_MASTERSALT="${IS_MASTERSALT:-}"
    IS_MASTERSALT_MASTER="${IS_MASTERSALT_MASTER:-}"
    IS_MASTERSALT_MINION="${IS_MASTERSALT_MINION:-}"
    STATES_URL="${STATES_URL:-"https://github.com/makinacorpus/makina-states.git"}"
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
    NICKNAME_FQDN="$(get_minion_id)"
    HOST="$(echo "${NICKNAME_FQDN}"|awk -F'.' '{print $1}')"
    if [ "x$(echo "${NICKNAME_FQDN}"|grep -q \.;echo ${?})" = "x0" ];then
        DOMAINNAME="$(echo "${NICKNAME_FQDN}"|sed -e "s/^[^.]*\.//g")"
    else
        DOMAINNAME="local"
        NICKNAME_FQDN="${HOST}.${DOMAINNAME}"
    fi

    # select the daemons to install but also
    # detect what is already present on the system
    if [ "x${SALT_CONTROLLER}" = "xsalt_master" ];then
        IS_SALT_MASTER="y"
    else
        IS_SALT_MINION="y"
    fi
    if [ "x${MASTERSALT_CONTROLLER}" = "xmastersalt_master" ];then
        IS_MASTERSALT_MASTER="y"
    elif [ "x${MASTERSALT_CONTROLLER}" = "xmastersalt_minion" ];then
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
    if [ "x${SALT_CLOUD}" = "x" ];then
        if [ -e "${ETC_INIT}.d/mastersalt-master" ]\
            || [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            MASTERSALT_INIT_PRESENT="y"
        fi
    fi
    if [ "x${MASTERSALT_INIT_PRESENT}" != "x" ]\
        || [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
        IS_MASTERSALT="y"
        IS_MASTERSALT_MASTER="y"
        IS_MASTERSALT_MINION="y"
    fi
    if [ "x${SALT_CLOUD}" != "x" ];then
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
        # - if we have not defined a mastersalt host,
        #    default to mastersalt.makina-corpus.net
        if [ "x${IS_MASTERSALT}" != "x" ];then
            if [ "x${MASTERSALT}" = "x" ];then
                MASTERSALT="${MASTERSALT_MAKINA_HOSTNAME}"
            fi
        fi
        if [ "x${SALT_CLOUD}" != "x" ] && [ -e "${SALT_CLOUD_DIR}/minion" ];then
             MASTERSALT="$(egrep "^master:" "${SALT_CLOUD_DIR}"/minion|awk '{print $2}'|sed -e "s/ //")"
             MASTERSALT_MASTER_DNS="${MASTERSALT}"
             MASTERSALT_MASTER_IP="${MASTERSALT}"
             MASTERSALT_MASTER_PORT="$(egrep "^master_port:" "${SALT_CLOUD_DIR}"/minion|awk '{print $2}'|sed -e "s/ //")"
        fi
        if [ "x${SALT_CLOUD}" = "x" ] && [ -e "${MASTERSALT_PILLAR}/mastersalt.sls" ];then
            MASTERSALT="$(grep "master: " ${MASTERSALT_PILLAR}/mastersalt.sls |awk '{print $2}'|tail -n 1)"
        fi

        MASTERSALT_MASTER_DNS="${MASTERSALT_MASTER_DNS:-${MASTERSALT}}"
        MASTERSALT_MASTER_IP="${MASTERSALT_MASTER_IP:-$(dns_resolve ${MASTERSALT_MASTER_DNS})}"
        MASTERSALT_MASTER_PORT="${MASTERSALT_MASTER_PORT:-"${MASTERSALT_PORT:-"4606"}"}"
        MASTERSALT_MASTER_PUBLISH_PORT="$(( ${MASTERSALT_MASTER_PORT} - 1 ))"

        MASTERSALT_MINION_DNS="${MASTERSALT_MINION_DNS:-"localhost"}"
        MASTERSALT_MINION_ID="$(mastersalt_get_minion_id)"
        MASTERSALT_MINION_IP="$(dns_resolve ${MASTERSALT_MINION_DNS})"

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
        if [ "x${SALT_CLOUD}" != "x" ];then
            if [ "x${IS_MASTERSALT}" = "x" ] && [ -e "${SALT_CLOUD_DIR}/minion" ];then
                SALT_MASTER_DNS_DEFAULT="$(egrep "^master:" "${SALT_CLOUD_DIR}"/minion|awk '{print $2}'|sed -e "s/ //")"
                SALT_MASTER_IP_DEFAULT="${SALT_MASTER_DNS_DEFAULT}"
                SALT_MASTER_PORT_DEFAULT="$(egrep "^master_port:" "${SALT_CLOUD_DIR}"/minion|awk '{print $2}'|sed -e "s/ //")"
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

    # --------- PROJECT VARS
    MAKINA_PROJECTS="makina-projects"
    PROJECTS_PATH="/srv/projects"
    PROJECT_URL="${PROJECT_URL:-""}"
    PROJECT_BRANCH="${PROJECT_BRANCH:-salt}"
    PROJECT_NAME="${PROJECT_NAME:-}"

    if [ "x${PROJECT_URL}" != "x" ] && [ "x${PROJECT_NAME}" = "x" ];then
        PROJECT_NAME="$(basename $(echo ${PROJECT_URL}|"${SED}" "s/.git$//"))"
    fi
    if [ "x${PROJECT_URL}" != "x" ] && [ "x${PROJECT_NAME}" = "x" ];then
        die "Please provide a \${PROJECT_NAME}"
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

    PROJECT_TOPSLS="${PROJECT_TOPSLS:-}"
    PROJECT_PATH="$PROJECTS_PATH/${PROJECT_NAME}"
    PROJECTS_SALT_PATH="${SALT_ROOT}/$MAKINA_PROJECTS"
    PROJECTS_PILLAR_PATH="${SALT_PILLAR}/$MAKINA_PROJECTS"
    PROJECT_PILLAR_LINK="$PROJECTS_PILLAR_PATH/${PROJECT_NAME}"
    PROJECT_PILLAR_PATH="$PROJECTS_PATH/${PROJECT_NAME}/pillar"
    PROJECT_PILLAR_FILE="$PROJECT_PILLAR_PATH/init.sls"
    PROJECT_SALT_LINK="${SALT_ROOT}/$MAKINA_PROJECTS/${PROJECT_NAME}"
    PROJECT_SALT_PATH="$PROJECT_PATH/salt"
    PROJECT_TOPSLS_DEFAULT="$MAKINA_PROJECTS/${PROJECT_NAME}/top.sls"
    PROJECT_TOPSTATE_DEFAULT="${MAKINA_PROJECTS}.${PROJECT_NAME}.top"
    PROJECT_PILLAR_STATE="${MAKINA_PROJECTS}.${PROJECT_NAME}"

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
    if [ "x${IS_MASTERSALT}" = "x" ];then
        store_conf bootsalt_mode mastersalt
    else
        store_conf bootsalt_mode salt
    fi

    # export variables to support a restart
    export TRAVIS_DEBUG SALT_BOOT_LIGHT_VARS
    export IS_SALT_UPGRADING SALT_BOOT_SYNC_CODE
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
    export BASE_PACKAGES STATES_URL SALT_BOOT_NOCONFIRM
    #
    export MASTERSALT_ROOT SALT_ROOT
    export SALT_PILLAR MASTERSALT_PILLAR
    export MASTERSALT_MS SALT_MS
    #
    export ROOT PREFIX ETC_INIT
    export VENV_PATH CONF_ROOT
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
    export MAKINA_PROJECTS PROJECTS_PATH PROJECT_URL
    export PROJECT_BRANCH PROJECT_NAME PROJECT_TOPSLS
    export PROJECT_PATH PROJECTS_SALT_PATH
    export PROJECTS_PILLAR_PATH PROJECT_PILLAR_LINK PROJECT_PILLAR_STATE
    export PROJECT_PILLAR_PATH PROJECT_PILLAR_FILE
    export PROJECT_SALT_LINK PROJECT_SALT_PATH
    export PROJECT_TOPSLS_DEFAULT PROJECT_TOPSTATE_DEFAULT
    #
    export MASTERSALT_BOOT_SKIP_HIGHSTATE SALT_BOOT_SKIP_HIGHSTATE SALT_BOOT_SKIP_HIGHSTATES
    #
    export SALT_CLOUD SALT_CLOUD_DIR
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
    bs_log "NICKNAME_FQDN/HOST/DOMAIN: ${NICKNAME_FQDN}/${HOST}/${DOMAINNAME}"
    bs_log "DATE: ${CHRONO}"
    bs_log "SALT_NODETYPE: $(get_salt_nodetype)"
    if [ "x${SALT_CLOUD}" != "x" ];then
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
    if [ "x${BUILDOUT_REBOOTSTRAP}" != "x" ];then
        bs_log "Rebootstrap buildout"
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
        for i in \
            "${MASTERSALT_MASTER_IP}" "${MASTERSALT_MINION_IP}";\
        do
            thistest="$(echo "${i}"|grep -q "${DNS_RESOLUTION_FAILED}")"
            if [ "x${thistest}" = "x0" ];then
                die "${DNS_RESOLUTION_FAILED}"
            fi
        done
    fi
    if [ "x${PROJECT_URL}" != "x" ];then
        bs_yellow_log "--------------------"
        bs_yellow_log "PROJECT variables:"
        bs_yellow_log "--------------------"
        bs_log "PROJECT_URL:  ${PROJECT_URL}"
        bs_log "PROJECT_BRANCH: ${PROJECT_BRANCH}"
        bs_log "PROJECT_NAME: ${PROJECT_NAME}"
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
    if [ "x$(dpkg-query -s ${@} 2>/dev/null|egrep "^Status:"|grep installed|wc -l|sed -e "s/ //g")"  = "x0" ];then
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
    for i in ${BASE_PACKAGES};do
        if [ "x$(dpkg-query -s ${i} 2>/dev/null|egrep "^Status:"|grep installed|wc -l|sed -e "s/ //g")" = "x0" ];then
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
    get_module_args "${SALT_ROOT}" "${SALT_MS}"
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
    if [ "x${last_salt_retcode}" != "x0" ] && [ "x${last_salt_retcode}" != "x2" ];then
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
        if egrep -q "result: false" "${outf}";then
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
    chrono="$(get_chrono)"
    if [ ! -d "${BOOT_LOGS}" ];then
        mkdir -pv "${BOOT_LOGS}"
    fi
    SALT_BOOT_OUTFILE="${BOOT_LOGS}/boot_salt.${chrono}.out"
    SALT_BOOT_LOGFILE="${BOOT_LOGS}/boot_salt.${chrono}.log"
    SALT_BOOT_CMDFILE="${BOOT_LOGS}/boot_salt_cmd"
    salt_call_wrapper_ "${SALT_MS}" $(get_saltcall_args) ${@}
}

mastersalt_call_wrapper() {
    chrono="$(get_chrono)"
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
    if [ "x${SALT_BOOT_IN_RESTART}" = "x" ];then
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
    minion_keys="$(find "${CONF_PREFIX}/pki/master/"{minions_pre,minions} -type f 2>/dev/null|wc -l|sed -e "s/ //g")"
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
                        git clone ${QUIET_GIT} "${STATES_URL}" "${ms}" &&\
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
                #"${SALT_MS}/_scripts/install_salt_modules.sh" "${SALT_ROOT}"
                cd "${ms}"
                if [ ! -d src ];then
                    mkdir src
                fi
                for i in "${ms}" "${ms}/src/"*;do
                    is_changeset=""
                    branch_pref=""
                    if [ -e "${i}/.git" ];then
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
                        if  [ "x${i}" = "x${ms}/src/SaltTesting" ]\
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
                            if [ "x$(git branch|egrep " ${co_branch}\$" |wc -l|sed -e "s/ //g")" != "x0" ];then
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
                                    [ "x${i}" = "x${ms}/src/SaltTesting" ]\
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

handle_upgrades() {
    /bin/true
    # stub for now
}

cleanup_previous_venv() {
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

setup_virtualenv() {
    # Script is now running in makina-states git location
    # Check for virtualenv presence
    REBOOTSTRAP="${VENV_REBOOTSTRAP:-${SALT_REBOOTSTRAP}}"
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
    cleanup_previous_venv ${SALT_MS}
    cleanup_previous_venv /srv/salt-venv
    cd ${SALT_MS}
    if     [ ! -e "${VENV_PATH}/bin/activate" ] \
        || [ ! -e "${VENV_PATH}/lib" ] \
        || [ ! -e "${VENV_PATH}/include" ] \
        ;then
        bs_log "Creating virtualenv in ${VENV_PATH}"
        virtualenv --no-site-packages --unzip-setuptools ${VENV_PATH} &&\
        . ${VENV_PATH}/bin/activate &&\
        easy_install -U setuptools &&\
        deactivate
        BUILDOUT_REBOOTSTRAP=y
        SALT_REBOOTSTRAP=y
    fi

    # virtualenv is present, activate it
    if [ -e "${VENV_PATH}/bin/activate" ];then
        if [ "x${QUIET}" = "x" ];then
            bs_log "Activating virtualenv in ${VENV_PATH}"
        fi
        . "${VENV_PATH}/bin/activate"
    fi
}

run_ms_buildout() {
    ms="${1}"
    cd "${ms}"
    # Check for buildout things presence
    if    [ ! -e "${ms}/bin/buildout" ]\
       || [ ! -e "${ms}/parts" ] \
       || [ "x${BUILDOUT_REBOOTSTRAP}" != "x" ] \
       || [ ! -e "${ms}/develop-eggs" ] \
        ;then
        bs_log "Launching buildout bootstrap for salt initialisation (${ms})"
        python bootstrap.py
        ret=${?}
        if [ "x${ret}" != "x0" ];then
            rm -rf "${ms}/parts" "${ms}/develop-eggs"
            die_ $ret " [bs] Failed buildout bootstrap (${ms})"
        fi
    fi
    # remove stale zmq egg (to relink on zmq3)
    test="$(ldd $(find -L "${ms}/eggs/pyzmq-"*egg -name *so 2>/dev/null) 2>/dev/null|grep zmq.so.1|wc -l|sed -e "s/ //g")"
    if [ "x${test}" != "x0" ];then
        find -L "${ms}/eggs/pyzmq-"*egg -maxdepth 0 -type d|xargs rm -rfv
    fi
    # detect incomplete buildout
    # pyzmq check is for testing upgrade from libzmq to zmq3
    if    [ ! -e "${ms}/bin/buildout" ]\
        || [ ! -e "${ms}/bin/salt-ssh" ]\
        || [ ! -e "${ms}/bin/salt" ]\
        || [ ! -e "${ms}/bin/salt-call" ]\
        || [ ! -e "${ms}/bin/salt-key" ]\
        || [ ! -e "${ms}/bin/salt-syndic" ]\
        || [ ! -e "${ms}/bin/mypy" ]\
        || [ ! -e "${ms}/.installed.cfg" ]\
        || [ "x$(find -L "${ms}/eggs/pyzmq"* |wc -l|sed -e "s/ //g")" = "x0" ]\
        || [ ! -e "${ms}/src/salt/setup.py" ]\
        || [ ! -e "${ms}/src/docker/setup.py" ]\
        || [ ! -e "${ms}/src/m2crypto/setup.py" ]\
        || [ ! -e "${ms}/src/SaltTesting/setup.py" ]\
        || [ -n "${BUILDOUT_REBOOTSTRAP}" ]\
        ;then
        cd "${ms}"
        bs_log "Launching buildout for salt initialisation (${ms})"
        bin/buildout || die " [bs] Failed buildout (${ms})"
        ret=${?}
        if [ "x${ret}" != "x0" ];then
            rm -rf "${ms}/.installed.cfg"
            die_ ${ret} " [bs] Failed buildout in ${ms}"
        fi
    fi
}

install_buildouts() {
    if [ "x${IS_SALT}" != "x" ];then
        run_ms_buildout ${SALT_MS}
    fi
    if [  "x${IS_MASTERSALT}" != "x" ];then
        if [ ! -e ${MASTERSALT_ROOT}/makina-states/.installed.cfg ];then
            bs_log "Copying base tree, this can take a while"
            # -a without time
            rsync -rlpgoD "${SALT_MS}/" "${MASTERSALT_ROOT}/makina-states/" --exclude=*pyc --exclude=*pyo --exclude=.installed.cfg --exclude=.mr.developer.cfg --exclude=.bootlogs
            cd ${MASTERSALT_ROOT}/makina-states
            rm -rf .installed.cfg .mr.developer.cfg parts
        fi
        run_ms_buildout "${MASTERSALT_ROOT}/makina-states/"
    fi
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

create_salt_skeleton(){
    branch_id="$(get_ms_branch|"${SED}" -e "s/changeset://g")"
    # create etc directory
    if [ ! -e "${CONF_PREFIX}" ];then mkdir "${CONF_PREFIX}";fi
    if [ ! -e "${CONF_PREFIX}/master.d" ];then mkdir "${CONF_PREFIX}/master.d";fi
    if [ ! -e "${CONF_PREFIX}/minion.d" ];then mkdir "${CONF_PREFIX}/minion.d";fi
    if [ ! -e "${CONF_PREFIX}/pki/master/minions" ];then mkdir -p "${CONF_PREFIX}/pki/master/minions";fi
    if [ ! -e "${CONF_PREFIX}/pki/minion" ];then mkdir -p "${CONF_PREFIX}/pki/minion";fi
    if [ ! -e "${CONF_PREFIX}/master" ];then
        cat > "${CONF_PREFIX}/master" << EOF
file_roots: {"base":["${SALT_ROOT}"]}
pillar_roots: {"base":["${SALT_PILLAR}"]}
runner_dirs: [${SALT_ROOT}/runners, ${SALT_MS}/mc_states/runners]
EOF
    fi
    if [ ! -e "${CONF_PREFIX}/minion" ];then
        cat > "${CONF_PREFIX}/minion" << EOF
id: $(get_minion_id)
master: $SALT_MASTER_DNS
master_port: ${SALT_MASTER_PORT}
file_roots: {"base":["${SALT_ROOT}"]}
pillar_roots: {"base":["${SALT_PILLAR}"]}
module_dirs: [${SALT_ROOT}/_modules, ${SALT_MS}/mc_states/modules]
returner_dirs: [${SALT_ROOT}/_returners, ${SALT_MS}/mc_states/returners]
states_dirs: [${SALT_ROOT}/_states, ${SALT_MS}/mc_states/states]
grain_dirs: [${SALT_ROOT}/_grains, ${SALT_MS}/mc_states/grains]
render_dirs: [${SALT_ROOT}/_renderers, ${SALT_MS}/mc_states/renderers]
EOF
    fi

    # create etc/mastersalt
    if [ "x${IS_MASTERSALT}" != "x" ];then
        if [ ! -e "${MCONF_PREFIX}" ];then mkdir "${MCONF_PREFIX}";fi
        if [ ! -e "${MCONF_PREFIX}/master.d" ];then mkdir "${MCONF_PREFIX}/master.d";fi
        if [ ! -e "${MCONF_PREFIX}/minion.d" ];then mkdir "${MCONF_PREFIX}/minion.d";fi
        if [ ! -e "${MCONF_PREFIX}/pki/master" ];then mkdir -p "${MCONF_PREFIX}/pki/master";fi
        if [ ! -e "${MCONF_PREFIX}/pki/minion" ];then mkdir -p "${MCONF_PREFIX}/pki/minion";fi
        if [ ! -e "${MCONF_PREFIX}/master" ];then
            cat > "${MCONF_PREFIX}/master" << EOF
file_roots: {"base":["${MASTERSALT_ROOT}"]}
pillar_roots: {"base":["${MASTERSALT_PILLAR}"]}
runner_dirs: [${MASTERSALT_ROOT}/runners, ${MASTERSALT_MS}/mc_states/runners]
EOF
        fi
        if [ ! -e "${MCONF_PREFIX}/minion" ];then
            cat > "${MCONF_PREFIX}/minion" << EOF
id: $(mastersalt_get_minion_id)
master: ${MASTERSALT_MASTER_DNS}
master_port: ${MASTERSALT_MASTER_PORT}
file_roots: {"base":["${MASTERSALT_ROOT}"]}
pillar_roots: {"base":["${MASTERSALT_PILLAR}"]}
module_dirs: [${MASTERSALT_ROOT}/_modules, ${MASTERSALT_MS}/mc_states/modules]
returner_dirs: [${MASTERSALT_ROOT}/_returners, ${MASTERSALT_MS}/mc_states/returners]
states_dirs: [${MASTERSALT_ROOT}/_states, ${MASTERSALT_MS}/mc_states/states]
grain_dirs: [${MASTERSALT_ROOT}/_grains, ${MASTERSALT_MS}/mc_states/grains]
render_dirs: [${MASTERSALT_ROOT}/_renderers, ${MASTERSALT_MS}/mc_states/renderers]
EOF
        fi
    fi
    # install salt cloud keys &  reconfigure any preprovisionned daemons
    if [ "x${SALT_CLOUD}" != "x" ];then
        bs_log "SaltCloud mode: killing daemons"
        if [ "x$(is_lxc)" != "x0" ];then
            regenerate_openssh_keys
        fi
        kill_ms_daemons
        # remove any provisionned init overrides
        if [ "x$(find /etc/init/*salt*.override 2>/dev/null|wc -l|sed "s/ //g")" != "x0" ];then
            bs_log "SaltCloud mode: removing init stoppers"
            rm -fv /etc/init/*salt*.override
        fi
        find "${CONF_PREFIX}"/minion* -type f 2>/dev/null|while read mfic;do
            bs_log "SaltCloud mode: Resetting salt minion conf ($(get_minion_id)/${SALT_MASTER_IP}/${SALT_MASTER_PORT}): ${mfic}"
            sed -i -e "s/^master:.*/master: ${SALT_MASTER_IP}/g" "${mfic}"
            sed -i -e "s/^id:.*$/id: $(get_minion_id)/g" "${mfic}"
            sed -i -e "s/^master_port:.*/master_port: ${SALT_MASTER_PORT}/g" "${mfic}"
        done
        find "${CONF_PREFIX}"/master* -type f 2>/dev/null|while read mfic;do
            bs_log "SaltCloud mode: Resetting salt master conf (${SALT_MASTER_IP}/${SALT_MASTER_PORT}/${SALT_MASTER_PUBLISH_PORT}): ${mfic}"
            sed -i -e "s/^interface:.*/interface: ${SALT_MASTER_IP}/g" "${mfic}"
            sed -i -e "s/^ret_port:.*/ret_port: ${SALT_MASTER_PORT}/g" "${mfic}"
            sed -i -e "s/^publish_port:.*/publish_port: ${SALT_MASTER_PUBLISH_PORT}/g" "${mfic}"
        done
        rm -f "${CONF_PREFIX}/pki/minion/minion_master.pub"
        if [ "x${IS_MASTERSALT}" != "x" ];then
            bs_log "SaltCloud mode: Resetting mastersalt minion keys"
            minion_dest="${MCONF_PREFIX}/pki/minion"
            master_dest="${MCONF_PREFIX}/pki/master"
            # regenerate keys for the local master
            if [ "x$(which salt-key 2>/dev/null)" != "x" ];then
                salt-key --gen-keys=master --gen-keys-dir=${CONF_PREFIX}/pki/master
            fi
            __install "${SALT_CLOUD_DIR}/minion.pem" "${minion_dest}/minion.pem"
            __install "${SALT_CLOUD_DIR}/minion.pub" "${minion_dest}/minion.pub"
            rm -f "${MCONF_PREFIX}/pki/minion/minion_master.pub"
            find "${MCONF_PREFIX}"/minion* -type f 2>/dev/null|while read mfic;do
                bs_log "SaltCloud mode: Resetting mastersalt minion conf ($(get_minion_id)/${MASTERSALT}/${MASTERSALT_MASTER_PORT}): ${mfic}"
                sed -i -e "s/^id:.*$/id: $(get_minion_id)/g" "${mfic}"
                sed -i -e "s/^master:.*$/master: ${MASTERSALT}/g" "${mfic}"
                sed -i -e "s/^master_port:.*$/master_port: ${MASTERSALT_MASTER_PORT}/g" "${mfic}"
            done
            # resetting local master minion's key
            find "${CONF_PREFIX}/pki/master" -name $(get_minion_id)|while read fic;do rm -fv "${fic}";done
        fi
        #if [ ! -d  "${CONF_PREFIX}/pki/master/minions" ];then
        #    mkdir "${CONF_PREFIX}/pki/master/minions"
        #fi
        #cp -f "${minion_dest}/minion.pub" "${CONF_PREFIX}/pki/master/minions/$(get_minion_id)"
        # duplicate key for mastersalt, uniq keypair for the 2 minions
        bs_log "SaltCloud mode: Installing keys"
        minion_dest="${CONF_PREFIX}/pki/minion"
        master_dest="${CONF_PREFIX}/pki/master"
        __install "${SALT_CLOUD_DIR}/minion.pem" "${minion_dest}/minion.pem"
        __install "${SALT_CLOUD_DIR}/minion.pub" "${minion_dest}/minion.pub"
        __install "${SALT_CLOUD_DIR}/minion.pub" "${master_dest}/minions/$(get_minion_id)"
        __install "${SALT_CLOUD_DIR}/master.pem" "${master_dest}/master.pem"
        __install "${SALT_CLOUD_DIR}/master.pub" "${master_dest}/master.pub"
        for i in "${MASTERSALT_PILLAR}/mastersalt.sls" "${SALT_PILLAR}/salt.sls";do
            if [ -e "$i" ];then
                bs_log "SaltCloud mode: removing ${i} default conf for it to be resetted"
                rm -f "${i}"
            fi
        done
        if [ "x${IS_SALT_MINION}" != "x" ];then
            if [ -e ${ETC_INIT}/salt-minion.conf ] || [ -e ${ETC_INIT}.d/salt-minion ];then
                lazy_start_salt_daemons
            fi
        fi
        if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
            if [ -e ${ETC_INIT}/mastersalt-minion.conf ] || [ -e ${ETC_INIT}.d/mastersalt-minion ];then
                lazy_start_mastersalt_daemons
            fi
        fi
    fi

    # create pillars
    SALT_PILLAR_ROOTS="${SALT_PILLAR}"
    if [ "x${IS_MASTERSALT}" != "x" ];then
        SALT_PILLAR_ROOTS="${SALT_PILLAR_ROOTS} ${MASTERSALT_PILLAR}"
    fi
    for pillar_root in ${SALT_PILLAR_ROOTS};do
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
    done
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
        if [ "x$(egrep -- "- makina-states\.top( |\t)*$" ${topf}|wc -l|sed -e "s/ //g")" = "x0" ];then
            debug_msg "Adding makina-states.top to ${topf}"
            "${SED}" -i -e "/['\"]\*['\"]:/ {
a\    - makina-states.top
}" "${topf}"
        fi
    done

    if [ "x$(grep -- "- salt" ${SALT_PILLAR}/top.sls 2>/dev/null|wc -l|sed -e "s/ //g")" = "x0" ];then
        debug_msg "Adding salt to default top salt pillar"
        "${SED}" -i -e "/['\"]\*['\"]:/ {
a\    - salt
}" "${SALT_PILLAR}/top.sls"
    fi
    # Create a default salt.sls in the pillar if not present
    if [ ! -e "${SALT_PILLAR}/salt.sls" ];then
        debug_msg "Creating default pillar's salt.sls"
        echo 'salt:' > "${SALT_PILLAR}/salt.sls"
    fi
    if [ "x$(grep "$BRANCH_PILLAR_ID" "${SALT_PILLAR}/salt.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
        echo "" >> "${SALT_PILLAR}/salt.sls"
        echo "${BRANCH_PILLAR_ID}" >> "${SALT_PILLAR}/salt.sls"
    fi
    "${SED}" -e "s/${BRANCH_PILLAR_ID}.*/$BRANCH_PILLAR_ID: ${branch_id}/g" -i "${SALT_PILLAR}/salt.sls"
    if [ "x$(egrep -- "^salt:" "${SALT_PILLAR}/salt.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
        echo ''  >> "${SALT_PILLAR}/salt.sls"
        echo 'salt:' >> "${SALT_PILLAR}/salt.sls"
    fi
    if [ "x$(egrep -- "( |\t)*minion:( |\t)*$" "${SALT_PILLAR}/salt.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
        debug_msg "Adding minion info to pillar"
        "${SED}" -i -e "/^salt:\( \|\t\)*$/ {
a\  minion:
a\    id: $(get_minion_id)
a\    interface: $SALT_MINION_IP
a\    master: $SALT_MASTER_DNS
a\    master_port: ${SALT_MASTER_PORT}
}" "${SALT_PILLAR}/salt.sls"
    fi
    if [ "x$(grep -- "id: $(get_minion_id)" "${SALT_PILLAR}/salt.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
        debug_msg "Adding salt minion id: $(get_minion_id)"
        "${SED}" -i -e "/^    id:/ d" "${SALT_PILLAR}/salt.sls"
        "${SED}" -i -e "/^  minion:/ {
a\    id: $(get_minion_id)
}" "${SALT_PILLAR}/salt.sls"
    # do no setup stuff for master for just a minion
    fi
    if [ "x${IS_SALT_MASTER}" != "x" ] \
       && [ "x$(egrep -- "( |\t)*master:( |\t)*$" "${SALT_PILLAR}/salt.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
        debug_msg "Adding master info to pillar"
        "${SED}" -i -e "/^salt:\( \|\t\)*$/ {
a\  master:
a\    interface: ${SALT_MASTER_IP}
a\    publish_port: $SALT_MASTER_PUBLISH_PORT
a\    ret_port: ${SALT_MASTER_PORT}
}" "${SALT_PILLAR}/salt.sls"
    fi
    # --------- MASTERSALT
    # Set default mastersalt  pillar
    if [ "x${IS_MASTERSALT}" != "x" ];then
        if [ "x$(grep -- "- mastersalt" "${MASTERSALT_PILLAR}/top.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
            debug_msg "Adding mastersalt info to top mastersalt pillar"
            "${SED}" -i -e "/['\"]\*['\"]:/ {
a\    - mastersalt
}" "${MASTERSALT_PILLAR}/top.sls"
        fi
        if [ ! -f "${MASTERSALT_PILLAR}/mastersalt.sls" ];then
            debug_msg "Creating mastersalt configuration file"
            echo "mastersalt:" >  "${MASTERSALT_PILLAR}/mastersalt.sls"
        fi
        if [ "x$(grep "${BRANCH_PILLAR_ID}" "${MASTERSALT_PILLAR}/mastersalt.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
            echo "" >> "${MASTERSALT_PILLAR}/mastersalt.sls"
            echo "$BRANCH_PILLAR_ID" >> "${MASTERSALT_PILLAR}/mastersalt.sls"
        fi
        "${SED}" -i -e "s/${BRANCH_PILLAR_ID}.*/$BRANCH_PILLAR_ID: ${branch_id}/g" "${MASTERSALT_PILLAR}/mastersalt.sls"
        if [ "x$(egrep -- "^mastersalt:( |\t)*$" "${MASTERSALT_PILLAR}/mastersalt.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
            echo ''  >> "${MASTERSALT_PILLAR}/mastersalt.sls"
            echo 'mastersalt:' >> "${MASTERSALT_PILLAR}/mastersalt.sls"
        fi
        if [ "x$(egrep -- "^( |\t)*minion:" "${MASTERSALT_PILLAR}/mastersalt.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
            debug_msg "Adding mastersalt minion info to mastersalt pillar"
            "${SED}" -i -e "/^mastersalt:\( \|\t\)*$/ {
a\  minion:
a\    id: $(mastersalt_get_minion_id)
a\    interface: ${MASTERSALT_MINION_IP}
a\    master: ${MASTERSALT_MASTER_DNS}
a\    master_port: ${MASTERSALT_MASTER_PORT}
}" "${MASTERSALT_PILLAR}/mastersalt.sls"
        fi
        if [ "x$(grep -- "id: $(mastersalt_get_minion_id)" "${MASTERSALT_PILLAR}/mastersalt.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
            debug_msg "Adding mastersalt minion id: $(mastersalt_get_minion_id)"
            "${SED}" -i -e "/^    id:/ d" "${MASTERSALT_PILLAR}/mastersalt.sls"
            "${SED}" -i -e "/^  minion:/ {
a\    id: $(mastersalt_get_minion_id)
}" "${MASTERSALT_PILLAR}/mastersalt.sls"
        fi
        if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            if [ "x$(egrep -- "( |\t)+master:( |\t)*$" "${MASTERSALT_PILLAR}/mastersalt.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
                debug_msg "Adding mastersalt master info to mastersalt pillar"
                "${SED}" -i -e "/^mastersalt:\( \|\t\)*$/ {
a\  master:
a\    interface: ${MASTERSALT_MASTER_IP}
a\    ret_port: ${MASTERSALT_MASTER_PORT}
a\    publish_port: ${MASTERSALT_MASTER_PUBLISH_PORT}
}" "${MASTERSALT_PILLAR}/mastersalt.sls"
            fi
        fi
    fi

    # reset minion_ids
    for i in $(find "${CONF_PREFIX}"/minion* -type f 2>/dev/null|grep -v sed);do
        "${SED}" -i -e "s/^#*id: .*/id: $(get_minion_id)/g" "${i}"
    done
    for i in $(find "${MCONF_PREFIX}"/minion* -type f 2>/dev/null|grep -v sed);do
        "${SED}" -i -e "s/^#*id: .*/id: $(mastersalt_get_minion_id)/g" "${i}"
    done
}

# ------------ SALT INSTALLATION PROCESS

mastersalt_master_processes() {
    ${PS} aux|grep salt-master|grep -v deploy.sh|grep -v boot-salt|grep mastersalt|grep -v grep|wc -l|sed -e "s/ //g"
}


mastersalt_minion_processes() {
    ${PS} aux|grep salt-minion|grep -v deploy.sh|grep -v boot-salt|grep mastersalt|grep -v grep|wc -l|sed -e "s/ //g"
}

master_processes() {
    ${PS} aux|grep salt-master|grep -v deploy.sh|grep -v boot-salt|grep -v mastersalt|grep -v grep|wc -l|sed -e "s/ //g"
}


minion_processes() {
    ${PS} aux|grep salt-minion|grep -v deploy.sh|grep -v boot-salt|grep -v mastersalt|grep -v grep|wc -l|sed -e "s/ //g"
}


lazy_start_salt_daemons() {
    if [ "x${IS_SALT_MASTER}" != "x" ];then
        if [ "x$(master_processes)" = "x0" ];then
            restart_local_masters
            sleep 2
        fi
        if [ "x$(master_processes)" = "x0" ];then
            die "Salt Master start failed"
        fi

    fi
    if [ "x${IS_SALT_MINION}" != "x" ];then
        if [ "x$(minion_processes)" = "x0" ];then
            restart_local_minions
            if [ "x${SALT_CLOUD}" = "x" ];then
                sleep 1
            else
                sleep 2
            fi
            if [ "x$(minion_processes)" = "x0" ];then
                die "Salt Minion start failed"
            fi
        fi
    fi

}

gen_mastersalt_keys() {
    if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
        if [ ! -e "${MCONF_PREFIX}/pki/master/master.pub" ];then
            bs_log "Generating mastersalt master key"
            salt-key --gen-keys=master --gen-keys-dir=${MCONF_PREFIX}/pki/master
        fi
    fi
    if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
        if [ ! -e "${MCONF_PREFIX}/pki/minion/minion.pub" ];then
            bs_log "Generating mastersalt minion key"
            salt-key --gen-keys=minion --gen-keys-dir=${MCONF_PREFIX}/pki/minion
        fi
    fi
    if [ "x${IS_MASTERSALT_MINION}" != "x" ]\
        && [ "x${IS_MASTERSALT_MASTER}" != "x" ]\
        && [ -e "${MCONF_PREFIX}/pki/minion/minion.pub" ];then
        __install "${MCONF_PREFIX}/pki/minion/minion.pub" "${MCONF_PREFIX}/pki/master/minions/$(get_minion_id)"
        __install "${MCONF_PREFIX}/pki/master/master.pub" "${MCONF_PREFIX}/pki/minion/minion_master.pub"
    fi
}

gen_salt_keys() {
    if [ "x${IS_SALT_MASTER}" != "x" ];then
        if [ ! -e "${CONF_PREFIX}/pki/master/master.pub" ];then
            bs_log "Generating salt minion key"
            salt-key --gen-keys=master --gen-keys-dir=${CONF_PREFIX}/pki/master
        fi
    fi
    # in saltcloude mode, keys are already providen
    if [ "x${SALT_CLOUD}" = "x" ];then
        if [ "x${IS_SALT_MINION}" != "x" ];then
            if [ ! -e "${CONF_PREFIX}/pki/minion/minion.pub" ];then
                bs_log "Generating salt minion key"
                salt-key --gen-keys=minion --gen-keys-dir=${CONF_PREFIX}/pki/minion
            fi
        fi
    fi
    if [ "x${IS_SALT_MINION}" != "x" ]\
       && [ "x${IS_SALT_MASTER}" != "x" ]\
       && [ -e "${CONF_PREFIX}/pki/minion/minion.pub" ];then
        __install "${CONF_PREFIX}/pki/minion/minion.pub" "${CONF_PREFIX}/pki/master/minions/$(get_minion_id)"
        __install "${CONF_PREFIX}/pki/master/master.pub" "${CONF_PREFIX}/pki/minion/minion_master.pub"
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
    # regenerate keys if missings
    if [ $(which salt-key 2>/dev/null) ];then
        gen_salt_keys
    fi
    if     [ ! -e "$CONF_PREFIX" ]\
        || [ ! -e "${CONF_PREFIX}/minion.d/00_global.conf" ]\
        || [ -e "${SALT_MS}/.rebootstrap" ]\
        || [ "x$(grep makina-states.controllers.salt_ "${CONF_PREFIX}/grains" 2>/dev/null |wc -l|sed -e "s/ //g")" = "x0" ]\
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
            sleep 10
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

kill_pids(){
    for i in ${@};do
        if [ "x$x{i}" != "x" ];then
            kill -9 ${i}
        fi
    done
}

killall_local_mastersalt_masters() {
    kill_pids $(${PS} aux|egrep "salt-(master|syndic)"|grep -v deploy.sh|grep -v boot-salt|grep mastersalt|awk '{print $2}') 1>/dev/null 2>/dev/null
}

killall_local_mastersalt_minions() {
    kill_pids $(${PS} aux|egrep "salt-(minion)"|grep -v deploy.sh|grep -v boot-salt|grep mastersalt|awk '{print $2}') 1>/dev/null 2>/dev/null
}

killall_local_masters() {
    kill_pids $(${PS} aux|egrep "salt-(master|syndic)"|grep -v deploy.sh|grep -v boot-salt|grep -v mastersalt|awk '{print $2}') 1>/dev/null 2>/dev/null
}

killall_local_minions() {
    kill_pids $(${PS} aux|egrep "salt-(minion)"|grep -v deploy.sh|grep -v boot-salt|grep -v mastersalt|awk '{print $2}') 1>/dev/null 2>/dev/null
}

restart_local_mastersalt_masters() {
    if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
        service mastersalt-master stop
        killall_local_mastersalt_masters
        service mastersalt-master restart
    fi
}

restart_local_mastersalt_minions() {
    if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
        service mastersalt-minion stop
        killall_local_mastersalt_minions
        service mastersalt-minion restart
    fi
}

restart_local_masters() {
    if [ "x${IS_SALT_MASTER}" != "x" ];then
        service salt-master stop
        killall_local_masters
        service salt-master restart
    fi
}

restart_local_minions() {
    if [ "x${IS_SALT_MINION}" != "x" ];then
        service salt-minion stop
        killall_local_minions
        service salt-minion restart
    fi
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
    challenged_ms=""
    global_tries="30"
    inner_tries="5"
    for i in `seq ${global_tries}`;do
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
    challenged_ms=""
    global_tries="30"
    inner_tries="5"
    for i in `seq ${global_tries}`;do
        restart_local_minions
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
    if [ "x$(check_connectivity ${SALT_MASTER_IP} ${SALT_MASTER_PORT} 30)" != "x0" ];then
        die "SaltMaster is unreachable (${SALT_MASTER_IP}/${SALT_MASTER_PORT})"
    fi
}

mastersalt_master_connectivity_check() {
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
    minion_keys="$(find ${CONF_PREFIX}/pki/master/minions -type f 2>/dev/null|wc -l|grep -v sed|sed -e "s/ //g")"
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
        service salt-minion restart
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
    if [ "x$(minion_processes)" = "x0" ];then
        restart_local_minions
        sleep $(get_delay_time)
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
                salt-key -y -a "${minion_id}"
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
    minion_id="$(mastersalt_get_minion_id)"
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
    minion_id="$(mastersalt_get_minion_id)"
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
        minion_id="$(mastersalt_get_minion_id)"
        if [ "x${minion_id}" = "x" ];then
            die "Minion did not start correctly, the minion_id cache file is always empty"
        fi
    fi
    if [ "x$(mastersalt_ping_test)" = "x0" ];then
        debug_msg "Mastersalt minion \"${minion_id}\" already registered on ${MASTERSALT}"
        salt_echo "changed=false comment='mastersalt minion already registered'"
    else
        if [ "x${MASTERSALT_MASTER_IP}" = "x127.0.0.1" ];then
            debug_msg "Forcing mastersalt master restart"
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
        mastersalt_master_connectivity_check
        bs_log "Waiting for mastersalt minion key hand-shake"
        minion_id="$(mastersalt_get_minion_id)"
        if [ "x$(salt_ping_test)" = "x0" ];then
            salt_echo "changed=yes comment='mastersalt minion registered'"
            bs_log "Salt minion \"${minion_id}\" registered on master"
            registered="1"
            salt_echo "changed=yes comment='salt minion registered'"
        else
            mastersalt_minion_challenge
            if [ "x${challenged_ms}" = "x" ];then
                bs_log "Failed accepting salt key on master for ${minion_id}"
                warn_log
                exit 1
            fi
            minion_id="$(mastersalt_get_minion_id)"
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
        if [ "x$(mastersalt_master_processes)" = "x0" ];then
            restart_local_mastersalt_masters
            sleep 2
            if [ "x$(mastersalt_master_processes)" = "x0" ];then
                die "Masteralt Master start failed"
            fi
        fi
    fi
    if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
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
            || [ "x$(grep makina-states.controllers.mastersalt_ "${MCONF_PREFIX}/grains" 2>/dev/null |wc -l|sed -e "s/ //g")" = "x0" ]\
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
    if [  "${SALT_BOOT_DEBUG}" != "x" ];then
        debug_msg "mastersalt:"
        debug_msg "RUN_MASTERSALT_BOOTSTRAP: $RUN_MASTERSALT_BOOTSTRAP"
        debug_msg "grains: $(grep makina-states.controllers.mastersalt_ "${MCONF_PREFIX}/grains" |wc -l|sed -e "s/ //g")"
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
        if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            debug_msg "Forcing mastersalt master restart"
            restart_local_mastersalt_masters
            sleep 10
        fi
        if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
        # restart mastersalt minion
            debug_msg "Forcing mastersalt minion restart"
            restart_local_mastersalt_minions
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

# -------------- MAKINA PROJECTS

maybe_install_projects() {
    if [ "x${PROJECT_URL}" != "x" ];then
        bs_log "Projects managment"
        project_grain="makina-states.projects.${PROJECT_NAME}.boot.top"
        BR=""
        if [ "x${PROJECT_BRANCH}" != "x" ];then
            BR="-b ${PROJECT_BRANCH}"
        fi
        FORCE_PROJECT_TOP="${FORCE_PROJECT_TOP:-}"
        # force state rerun if project is not there anymore
        if [ ! -e "${PROJECT_PATH}" ];then
            mkdir -pv "${PROJECT_PATH}"
        fi
        checkout=""
        if [ ! -e "${PROJECT_SALT_PATH}/.git/config" ];then
            bs_log "Cloning  ${PROJECT_URL}@$PROJECT_BRANCH in $PROJECT_SALT_PATH"
            git clone ${BR} "${PROJECT_URL}" "$PROJECT_SALT_PATH"
            ret="${?}"
            if [ "x${ret}" != "x0" ];then
                bs_log "Failed to download project from ${PROJECT_URL}, or maybe the salt states branch ${PROJECT_BRANCH} does not exist"
                exit 1
            fi
            if [ ! -e "${PROJECT_SALT_PATH}/.git/config" ];then
                bs_log "Incomplete download project from ${PROJECT_URL}, see ${PROJECT_SALT_PATH}"
                exit 1
            fi
            checkout="y"
            FORCE_PROJECT_TOP="y"
        fi
        if [ -h  "${PROJECT_SALT_LINK}" ];then
            rm -f "${PROJECT_SALT_LINK}"
        fi
        ln -sf "${PROJECT_SALT_PATH}" "${PROJECT_SALT_LINK}"
        changed="false"
        if [ -f "${SALT_ROOT}/${PROJECT_TOPSLS_DEFAULT}"  ] && [ "x${PROJECT_TOPSLS}" = "x" ];then
            PROJECT_TOPSLS="${PROJECT_TOPSLS_DEFAULT}"
        fi
        PROJECT_TOPSTATE="$(echo ${PROJECT_TOPSLS}|"${SED}" -e 's/\//./g'|"${SED}" -e 's/\.sls//g')"
        if [ ! -d "${PROJECT_PILLAR_PATH}" ];then
            mkdir -p "${PROJECT_PILLAR_PATH}"
            debug_msg "Creating pillar container in ${PROJECT_PILLAR_PATH}"
        fi
        if [ ! -d "${PROJECTS_PILLAR_PATH}" ];then
            mkdir -p "${PROJECTS_PILLAR_PATH}"
            debug_msg "Creating ${MAKINA_PROJECTS} pillar container in ${SALT_PILLAR}"
        fi
        if [ ! -e "${PROJECT_PILLAR_LINK}" ];then
            debug_msg "Linking project ${PROJECT_NAME} pillar in ${SALT_PILLAR}"
            ln -sfv "${PROJECT_PILLAR_PATH}" "${PROJECT_PILLAR_LINK}"
        fi
        if [ ! -e "${PROJECT_PILLAR_FILE}" ];then
            if [ ! -e "${PROJECT_SALT_PATH}/PILLAR.sample.sls" ];then
                debug_msg "Creating empty project ${PROJECT_NAME} pillar in ${PROJECT_PILLAR_FILE}"
                touch "${PROJECT_SALT_PATH}/PILLAR.sample.sls"
            fi
            debug_msg "Linking project ${PROJECT_NAME} pillar in ${PROJECT_PILLAR_FILE}"
            ln -sfv "${PROJECT_SALT_PATH}/PILLAR.sample.sls" "${PROJECT_PILLAR_FILE}"
        fi
        if [ "x$(grep -- "- ${PROJECT_PILLAR_STATE}" "${SALT_PILLAR}/top.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
            debug_msg "including ${PROJECT_NAME} pillar in ${SALT_PILLAR}/top.sls"
            "${SED}" -e "/['\"]\*['\"]:/ {
a\    - ${PROJECT_PILLAR_STATE}
}" -i "${SALT_PILLAR}/top.sls"
        fi
        O_SALT_BOOT_LOGFILE="${SALT_BOOT_LOGFILE}"
        O_SALT_BOOT_OUTFILE="${SALT_BOOT_OUTFILE}"
        if [ "x$(get_grain ${project_grain}|grep True|wc -l|sed -e "s/ //g")" != "x0" ] || [ "x${FORCE_PROJECT_TOP}" != "x" ];then
            if [ "x${PROJECT_TOPSLS}" != "x" ];then
                SALT_BOOT_LOGFILE="${PROJECT_SALT_PATH}/.salt_top_log.log"
                SALT_BOOT_OUTFILE="${PROJECT_SALT_PATH}/.salt_top_out.log"
                bs_log "Running salt Top state: ${PROJECT_URL}@$PROJECT_BRANCH[${PROJECT_TOPSLS}]"
                salt_call_wrapper state.sls "${PROJECT_TOPSTATE}"
                if [ "x${SALT_BOOT_DEBUG}" != "x" ];then
                    cat "${SALT_BOOT_OUTFILE}"
                fi
                if [ "x${last_salt_retcode}" != "x0" ];then
                    warn_log
                    bs_log "Failed to run ${PROJECT_TOPSLS}"
                    exit 1
                else
                    warn_log
                    if [ "x$(grep -- "- ${PROJECT_TOPSTATE}" "${SALT_ROOT}/top.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
                        if [ "x$(grep -- " - makina-states.top" "${SALT_ROOT}/top.sls"|wc -l|sed -e "s/ //g")" != "x0" ];then
                            "${SED}" -i -e "/ - makina-states.top/ {
a\    - ${PROJECT_TOPSTATE}
}" "${SALT_ROOT}/top.sls"
                        else
                            debug_msg "including ${PROJECT_NAME} pillar in ${SALT_ROOT}/top.sls"
                            "${SED}" -i -e "/['\"]\*['\"]:/ {
a\    - ${PROJECT_TOPSTATE}
}" "${SALT_ROOT}/top.sls"
                        fi
                    fi
                    set_grain "${project_grain}"
                    if [ "x${last_salt_retcode}" != "x0" ];then
                        warn_log
                        bs_log "Failed to set project grain: ${project_grain}"
                        exit 1
                    fi
                fi
                changed="true"
            fi
        else
            bs_log "Top state: ${PROJECT_URL}@$PROJECT_BRANCH[${PROJECT_TOPSLS}] already done (remove grain: $project_grain to redo)"
            salt_echo "changed=\"false\" comment=\"${PROJECT_URL}@$PROJECT_BRANCH[${PROJECT_TOPSLS}] already done\""
        fi
        if [ "x$(grep -- "- ${PROJECT_TOPSTATE}" "${SALT_ROOT}/top.sls"|wc -l|sed -e "s/ //g")" = "x0" ];then
            "${SED}" -i -e "/['\"]\*['\"]:/ {
a\    - ${PROJECT_TOPSTATE}
}" "${SALT_ROOT}/top.sls"
        fi
        bs_log "Installation finished, dont forget to install/verify:"
        bs_log "    - ${PROJECT_TOPSLS} in ${SALT_ROOT}/top.sls"
        bs_log "    - in ${PROJECT_PILLAR_FILE}"
        if [ "x${changed}" = "xfalse" ];then
            salt_echo "changed=\"${changed}\" comment=\"already installed\""
        else
            salt_echo "changed=\"${changed}\" comment=\"installed\""
        fi
        SALT_BOOT_LOGFILE="${O_SALT_BOOT_LOGFILE}"
        SALT_BOOT_OUTFILE="${O_SALT_BOOT_OUTFILE}"
    fi
}

cleanup_old_installs() {
    master_conf="${CONF_PREFIX}/master.d/00_global.conf"
    minion_conf="${CONF_PREFIX}/minion.d/00_global.conf"
    mmaster_conf="${MCONF_PREFIX}/master.d/00_global.conf"
    mminion_conf="${MCONF_PREFIX}/minion.d/00_global.conf"
    # _moduleName/mc_moduleName to mc_states/modules
    # ext_mod/mc_states/modules to mc_states/modules
    # ext_mod/modules to mc_states/modules
    # ext_mod/mc_modules to mc_states/mc_modules
    minion_cfg="${CONF_PREFIX}/minion"
    if [ -e "${CONF_PREFIX}/minion.d/00_global.conf" ];then
        minion_cfg="${CONF_PREFIX}/minion.d/00_global.conf"
    fi
    if [ -e "${minion_cfg}" ];then
        for i in module returner renderer state grain;do
            key="${i}"
            if [ "x${i}" = "xstate" ];then
                key="${i}s"
            fi
            if [ "x${i}" = "xrenderer" ];then
                key="render"
            fi
            if [ "x$(egrep "^${key}_dirs:" "${minion_cfg}"|wc -l|sed -e "s/ //g")" = "x0" ];then
                echo "${key}_dirs: [${SALT_ROOT}/_${i}s, ${SALT_MS}/mc_states/${i}s]" >> "${minion_cfg}"
            fi
        done
    fi
    mminion_cfg="${MCONF_PREFIX}/minion"
    if [ -e "${MCONF_PREFIX}/minion.d/00_global.conf" ];then
        mminion_cfg="${MCONF_PREFIX}/minion.d/00_global.conf"
    fi
    if [ -e "${mminion_cfg}" ];then
        for i in module returner renderer state grain;do
            key="${i}"
            if [ "x${i}" = "xstate" ];then
                key="${i}s"
            fi
            if [ "x${i}" = "xrenderer" ];then
                key="render"
            fi
            if [ "x$(egrep "^${key}_dirs:" "${mminion_cfg}" 2>/dev/null|wc -l|sed -e "s/ //g")" = "x0" ];then
                echo "${key}_dirs: [${MASTERSALT_ROOT}/_${i}s, ${MASTERSALT_MS}/mc_states/${i}s]" >> "${mminion_cfg}"
            fi
        done
    fi
    for conf in "${minion_conf}" "${mminion_conf}";do
        if [ -e "$conf" ];then
            if [ "x$(egrep "^grain_dirs:" "${conf}"|wc -l|sed -e "s/ //g")" = "x0" ];then
                bs_log "Patching grains_dirs -> grain_dirs in ${conf}"
                "${SED}" -i -e "s:grains_dirs:grain_dirs:g" "${conf}"
            fi
            for i in grains modules renderers returners states;do
                if [ "x$(grep "makina-states/mc_states/${i}" "${conf}"|wc -l|sed -e "s/ //g")" = "x0" ];then
                    bs_log "Patching ext_mods/${i} to mc_states/${i} in $conf"
                    new_path="makina-states/mc_states/${i}"
                    "${SED}" -i -e "s:makina-states/_${i}:${new_path}:g" "$conf"
                    "${SED}" -i -e "s:makina-states/_${i}/mc_${i}:${new_path}:g" "$conf"
                    "${SED}" -i -e "s:makina-states/ext_mods/mc_states/${i}:${new_path}:g" "$conf"
                    "${SED}" -i -e "s:makina-states/ext_mods/${i}:${new_path}:g" "$conf"
                    "${SED}" -i -e "s:makina-states/ext_mods/mc_${i}:${new_path}:g" "$conf"
                    "${SED}" -i -e "s:makina-states/mc_salt/mc_${i}:${new_path}:g" "$conf"
                fi
            done
        fi
    done
    for conf in "${master_conf}" "${mmaster_conf}";do
        if [ -e "$conf" ];then
            for i in runners;do
                if [ "x$(grep "makina-states/mc_states/${i}" "${conf}"|wc -l|sed -e "s/ //g")" = "x0" ];then
                    bs_log "Patching ext_mods/${i} to mc_states/mc_${i} in ${conf}"
                    new_path="makina-states/mc_states/${i}"
                    "${SED}" -i -e "s:makina-states/_${i}:${new_path}:g" "$conf"
                    "${SED}" -i -e "s:makina-states/_${i}/mc_${i}:${new_path}:g" "$conf"
                    "${SED}" -i -e "s:makina-states/ext_mods/mc_states/${i}:${new_path}:g" "$conf"
                    "${SED}" -i -e "s:makina-states/ext_mods/${i}:${new_path}:g" "$conf"
                    "${SED}" -i -e "s:makina-states/ext_mods/mc_${i}:${new_path}:g" "$conf"
                    "${SED}" -i -e "s:makina-states/mc_salt/mc_${i}:${new_path}:g" "$conf"
                fi
            done
        fi
    done
    for i in "${MASTERSALT_ROOT}" "${SALT_ROOT}";do
        if [ -h "${i}/_grains/makina_grains.py" ];then
            rm -f "${i}/_grains/makina_grains.py"
        fi
    done
    for i in "${SALT_ROOT}" "${MASTERSALT_ROOT}";do
        if [ "x$(grep "makina-states.setup" "${i}/setup.sls" 2> /dev/null|wc -l|sed -e "s/ //g")" != "x0" ];then
            rm -rfv "${i}/setup.sls"
        fi
    done
    for i in "${SALT_MS}" "${MASTERSALT_MS}";do
        if [ -e "${i}" ];then
            for j in "${i}/bin/"mastersalt*;do
                if [ -e "$j" ];then
                    bs_log "Cleanup $j"
                    rm -rvf "$j"
                fi
            done
        fi
    done
    if [ ! -d "${MASTERSALT_PILLAR}" ] \
        && [ -e "${SALT_PILLAR}/mastersalt.sls" ] \
        && [ -e ${BIN_DIR}/mastersalt ];then
        bs_log "copy old pillar to new ${MASTERSALT_PILLAR}"
        cp -rf "${SALT_PILLAR}" "${MASTERSALT_PILLAR}"
        rm -vf "${SALT_PILLAR}/mastersalt.sls"
        if [ -e "${MASTERSALT_PILLAR}/salt.sls" ];then
            rm -vf "${MASTERSALT_PILLAR}/salt.sls"
        fi
        if [ "x${IS_SALT}" != "x" ];then
            "${SED}" -i -e "/^\( \|\t\)*- mastersalt$/d" "${SALT_PILLAR}/top.sls"
        fi
        if [ "x${IS_MASTERSALT}" != "x" ];then
            "${SED}" -i -e "/^\( \|\t\)*- salt$/d" "${MASTERSALT_PILLAR}/top.sls"
        fi
    fi
    ls \
        "${MASTERSALT_ROOT}/_modules/mc_apache.py"*\
        "${MASTERSALT_ROOT}/_modules/mc_utils.py"*\
        "${MASTERSALT_ROOT}/_states/bacula.py"*\
        "${MASTERSALT_ROOT}/_states/mc_apache.py"*\
        "${SALT_ROOT}/_modules/mc_apache.py"*\
        "${SALT_ROOT}/_modules/mc_utils.py"*\
        "${SALT_ROOT}/_states/bacula.py"*\
        "${SALT_ROOT}/_states/mc_apache.py"* \
        "${MASTERSALT_MS}/_modules/mc_apache.py"*\
        "${MASTERSALT_MS}/_modules/mc_utils.py"*\
        "${MASTERSALT_MS}/_states/bacula.py"*\
        "${MASTERSALT_MS}/_states/mc_apache.py"*\
        "${SALT_MS}/_modules/mc_apache.py"*\
        "${SALT_MS}/_modules/mc_utils.py"*\
        "${SALT_MS}/_states/bacula.py"*\
        "${SALT_MS}/_states/mc_apache.py"* \
        2>/dev/null|while read oldmode;do
        rm -fv "${oldmode}"
    done
    ls -d \
        "${MASTERSALT_MS}/_modules/"    \
        "${MASTERSALT_MS}/_states/"     \
        "${MASTERSALT_MS}/_runners/"    \
        "${MASTERSALT_MS}/_returners/"  \
        "${MASTERSALT_MS}/_renderers/"  \
        "${SALT_MS}/_modules/"    \
        "${SALT_MS}/_states/"     \
        "${SALT_MS}/_runners/"    \
        "${SALT_MS}/_returners/"  \
        "${SALT_MS}/_renderers/"  \
        2>/dev/null|while read oldmode;do
        rm -frv "${oldmode}"
    done
    if [ "x$(egrep "bootstrapped\.salt" ${MCONF_PREFIX}/grains 2>/dev/null |wc -l|sed -e "s/ //g")" != "x0" ];then
        bs_log "Cleanup old mastersalt grains"
        "${SED}" -i -e "/bootstrap\.salt/d" "${MCONF_PREFIX}/grains"
        mastersalt_call_wrapper --local saltutil.sync_grains
    fi
    if [ "x$(grep mastersalt ${CONF_PREFIX}/grains 2>/dev/null |wc -l|sed -e "s/ //g")" != "x0" ];then
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
        bs_log "Examples:"
        exemple ":" "install a saltmaster/minion:"
        exemple " --nodetype=devhost:" "install a saltmaster/minion in 'development' mode"
        exemple " --mastersalt mastersalt.mycompany.net:" "install a mastersalt minion linked to mastersalt.mycompany.net"
        exemple " --project-url http://github.com/salt/foo.git:" "install the foo project from the salt branch of https://github.com/salt/foo.git"
    fi
    echo;echo
    bs_log "General settings:"
    bs_help "-h|--help:" "this help message" "" y
    bs_help "-l|--long-help:" "this help message + aditionnal help and advanced settings" "" y
    bs_help "-C|--no-confirm:" "Do not ask for start confirmation" "" y
    bs_help "-S|--skip-checkouts:" "Skip initial checkouts / updates" "" y
    bs_help "-s|--skip-highstates:" "Skip highstates" "" y
    bs_help "--upgrade" "Run bootsalt upgrade code (primarely destinated to run as the highstate wrapper to use in crons)" "" "${IS_SALT_UPGRADING}"
    bs_help "-d|--debug:" "debug/verbose mode" "NOT SET" y
    bs_help "-b|--branch <branch>" "MakinaStates branch to use" "${MS_BRANCH}" y
    bs_help "--debug-level <level>:" "debug level (quiet|all|info|error)" "NOT SET" y

    echo;echo
    bs_log "Server settings:"
    bs_help "-n|--nodetype <nt>:" "Nodetype to install into (devhost | server | dockercontainer | lxcontainer | vm | vagrantvm )" "$(get_salt_nodetype)" "y"
    echo
    bs_log "Salt settings:"
    bs_help "--no-salt:" "Do not install salt daemons" "" y
    bs_help "-no-M|--no-salt-master:" "Do not install a salt master" "${IS_SALT_MASTER}" y
    bs_help "-m|--minion-id:" "Minion id" "$(get_minion_id)" y
    bs_help "--mastersalt-minion-id:" "Mastersalt minion id (default to minionid)" "$(mastersalt_get_minion_id)" y
    bs_help "--salt-master-dns <hostname>:" "DNS of the salt master" "${SALT_MASTER_DNS}" y
    bs_help "--salt-master-port <port>:"        "Port of the salt master" "${MASTERSALT_MASTER_PORT}" y
    echo
    bs_log "Mastersalt settings (if any):"
    printf "    ${YELLOW} by default, we only install a minion, unless you add -MM${NORMAL}\n"
    bs_help "--mastersalt <dns>:" "DNS of the mastersalt master" "${MASTERSALT_MASTER_DNS}" y
    bs_help "--mastersalt-master-port <port>:"  "Port of the mastersalt master" "${MASTERSALT_MASTER_PORT}" y
    bs_help "--no-mastersalt:" "Do not install mastersalt daemons" "" y
    bs_help "-NN|--mastersalt-minion:" "install a mastersalt minion" "${IS_MASTERSALT_MINION}" y
    bs_help "-MM|--mastersalt-master:" "install a mastersalt master" "${IS_MASTERSALT_MASTER}" y
    echo
    bs_log "Project settings (if any):"
    bs_help "-u|--project-url <url>:" "project url to get to install this project (set to blank to only install makina-states)"
    bs_help "-B|--project-name <name>:" "Project name" "" "y"
    bs_help "--project-branch <branch>:" "salt branch to install the project, to use a specific changeset, use changeset:COMMIT_ID"  "${PROJECT_BRANCH}" y

    if [ "x${SALT_LONG_HELP}" != "x" ];then
        echo
        bs_log "Advanced settings:"
        bs_help "--kill:" "Kill all daemons" "${SALT_BOOT_CLEANUP}" y
        bs_help "--cleanup:" "Cleanup old execution logfiles" "${SALT_BOOT_CLEANUP}" y
        bs_help "--synchronize-code:" "Only sync sourcecode" "${SALT_BOOT_SYNC_CODE}" y
        bs_help "--check-alive" "restart daemons if they are down" "" "y"
        bs_help "--restart-daemons" "restart master & minions daemons" "" "y"
        bs_help "--restart-masters" "restart master daemons" "" "y"
        bs_help "--restart-minions" "restart minion daemons" "" "y"
        bs_help "--no-colors:" "No terminal colors" "${NO_COLORS}" "y"
        bs_help "--salt-rebootstrap:" "Redo salt bootstrap" "${SALT_REBOOTSTRAP}" "y"
        bs_help "--buildout-rebootstrap:" "Redo buildout bootstrap" "${BUILDOUT_REBOOTSTRAP}" "y"
        bs_help "--venv-rebootstrap:" "Redo venv, buildout & salt bootstrap" "${VENV_REBOOTSTRAP}" "y"
        bs_help "--test:" "run makina-states tests, be caution, this installs everything and is to be installed on a vm which will be trashed afterwards!" "${MAKINASTATES_TEST}" "y"
        bs_help "--salt-minion-dns <dns>:" "DNS of the salt minion" "${SALT_MINION_DNS}" "y"
        bs_help "-g|--makina-states-url <url>:" "makina-states url" "${STATES_URL}" y
        bs_help "-r|--root <path>:" "/ path" "${ROOT}"
        bs_help "--salt-root <path>:" "Salt root installation path" "${SALT_ROOT}" y
        bs_help "--conf-root <path>:" "Salt configuration container path" "${CONF_ROOT}" y
        bs_help "-p|--prefix <path>:" "prefix path" "${PREFIX}" y
        bs_help "-P|--pillar <path>:" "pillar path" "${SALT_PILLAR}" y
        bs_help "-M|--salt-master:" "install a salt master" "${IS_SALT_MASTER}" y
        bs_help "-N|--salt-minion:" "install a salt minion" "${IS_SALT_MINION}" y
        bs_help "-no-N|--no-salt-minion:" "Do not install a salt minion" "${IS_SALT_MINION}" y
        #bs_help "-mac|--master-controller <controller>:" "makina-states controller to use for the master" "$SALT_MASTER_CONTROLLER" y
        #bs_help "-mic|--minion-controller <controller>:" "makina-states controller to use for the minion" "$SALT_MINION_CONTROLLER" y
        bs_help "--salt-master-publish-port:" "Salt master publish port" "${SALT_MASTER_PUBLISH_PORT}" y

        bs_log "  Mastersalt settings (if any):"
        bs_help "--mconf-root <path>:" "Mastersalt configuration container path" "${CONF_ROOT}" y
        bs_help "--mastersalt-root <path>:" "MasterSalt root installation path" "${SALT_ROOT}" y
        bs_help "-PP|--mastersalt-pillar <path>:" "mastersalt pillar path" "${MASTERSALT_PILLAR}"  y
        bs_help "--mastersalt-minion-dns <dns>:"  "DNS of the mastersalt minion" "${MASTERSALT_MINION_DNS}" y
        bs_help "--salt-master-ip <ip>:"  "IP of the salt master" "${SALT_MASTER_IP}" y
        bs_help "--mastersalt-master-ip <ip>:"  "IP of the mastersalt master" "${MASTERSALT_MASTER_IP}" y
        bs_help "--mastersalt-master-publish-port <port>:" "MasterSalt master publish port" "${MASTERSALT_MASTER_PUBLISH_PORT}" y
        #bs_help "-mmac|--mastersalt-master-controller <controller>:" "makina-states controller to use for the mastersalt master" "${MASTERSALT}_MINION_CONTROLLER"   y
        #bs_help "-mmic|--mastersalt-minion-controller <controller>:" "makina-states controller to use for the mastersalt minion" "${MASTERSALT}_MASTER_CONTROLLER"  y
        bs_help "-no-MM|--no-mastersalt-master:" "do not install a mastersalt master" "${IS_MASTERSALT_MASTER}" y
        bs_help "-no-NN|--no-mastersalt-minion:" "do not install a mastersalt minion" "${IS_MASTERSALT_MINION}" y

        bs_log "  Project settings (if any):"
        bs_help "--projects-path <path>:" "projects root path" "${PROJECTS_PATH}" y
        bs_help "--project-top <sls>:" "project SLS file to execute"  "${PROJECT_TOPSLS}" y
    fi
}

maybe_run_tests() {
    if [ "x${MAKINASTATES_TEST}" = "x" ];then return;fi
    bs_log "Running makinastates tests"
    salt_call_wrapper state.sls makina-states.tests
    if [ "x${SALT_BOOT_DEBUG}" != "x" ];then cat "${SALT_BOOT_OUTFILE}";fi
    warn_log
    if [  -e /tmp/testok ];then
        bs_log "Marker for test ok is not there"
        exit -2
    elif [ "x${last_salt_retcode}" != "x0" ];then
        bs_log "Failed tests for makina states !"
        exit 1
    else
        if [  -e /tmp/testok ];then
            rm -f /tmp/testok
        fi
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
        if [ "x${1}" = "x--cleanup" ];then
            SALT_BOOT_CLEANUP="1";argmatch="1"
        fi
        if [ "x${1}" = "x--from-salt-cloud" ];then
            SALT_CLOUD="1"
            argmatch="1"
            SALT_BOOT_SKIP_HIGHSTATES="1"
        fi
        if [ "x${1}" = "x-q" ] || [ "x${1}" = "x--quiet" ];then
            QUIET="1";argmatch="1"
        fi
        if [ "x${1}" = "x-h" ] || [ "x${1}" = "x--help" ];then
            USAGE="1";argmatch="1"
        fi
        if [ "x${1}" = "x-d" ] || [ "x${1}" = "x--debug" ];then
            SALT_BOOT_DEBUG="y";argmatch="1"
        fi
        if [ "x${1}" = "x--no-colors" ];then
            NO_COLORS="1";argmatch="1"
        fi
        if [ "x${1}" = "x--upgrade" ];then
            IS_SALT_UPGRADING="1";argmatch="1"
        fi
        if [ "x${1}" = "x--test" ];then
            MAKINASTATES_TEST=1;argmatch="1"
        fi
        if [ "x${1}" = "x-l" ] || [ "x${1}" = "x--long-help" ];then
            SALT_LONG_HELP="1";USAGE="1";argmatch="1"
        fi
        if [ "x${1}" = "x--salt-rebootstrap" ];then
            SALT_REBOOTSTRAP="1";argmatch="1"
        fi
        if [ "x${1}" = "x--buildout-rebootstrap" ];then
            BUILDOUT_REBOOTSTRAP=1;argmatch="1"
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
            STATES_URL="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--mastersalt" ];then
            MASTERSALT="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-r" ] || [ "x${1}" = "x--root" ];then
            ROOT="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--salt-root" ];then
            SALT_ROOT="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--mastersalt-root" ];then
            MASTERSALT_ROOT="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--conf-root" ];then
            CONF_ROOT="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--mconf-root" ];then
            MCONF_ROOT="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-p" ] || [ "x${1}" = "x--prefix" ];then
            PREFIX="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-P" ] || [ "x${1}" = "x--pillar" ];then
            SALT_PILLAR="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-PP" ] || [ "x${1}" = "x--mastersalt-pillar" ];then
            MASTERSALT_PILLAR="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-u" ] || [ "x${1}" = "x--project-url" ];then
            PROJECT_URL="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-B" ] || [ "x${1}" = "x--project-name" ];then
            PROJECT_NAME="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-b" ] || [ "x${1}" = "x--branch" ];then
            FORCE_MS_BRANCH=1;MS_BRANCH="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--project-branch" ];then
            PROJECT_BRANCH="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--project-top" ];then
            PROJECT_TOPSLS="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--projects-path" ];then
            PROJECTS_PATH="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--debug-level" ];then
            SALT_BOOT_DEBUG_LEVEL="${2}";sh="2";argmatch="1"
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

check_alive() {
    restart_modes=""
    # kill all check alive
    ps -eo pid,etimes,cmd|sort -n -k2|egrep "boot-salt.*alive"|grep -v grep|while read psline;
    do
        seconds="$(echo "$psline"|awk '{print $2}')"
        pid="$(echo $psline|awk '{print $1}')"
        if [ "${seconds}" -gt "300" ];then
            bs_log "something was wrong with last restart, killing old check alive process: $pid"
            bs_log "${psline}"
            kill -9 "${pid}"
            touch /tmp/bootsaltmode
        fi
    done
    # kill all old (master)salt call (> 12 hours)
    ps -eo pid,etimes,cmd|sort -n -k2|egrep "salt-call"|grep -v grep|while read psline;
    do
        seconds="$(echo "$psline"|awk '{print $2}')"
        pid="$(echo $psline|awk '{print $1}')"
        if [ "${seconds}" -gt "$((60*60*12))" ];then
            bs_log "Something went wrong with last restart, killing old salt call process: $pid"
            bs_log "$psline"
            kill -9 "${pid}"
            touch /tmp/bootsaltmode
        fi
    done
    # kill all old (master)salt ping call (> 120 sec)
    ps -eo pid,etimes,cmd|sort -n -k2|egrep "salt-call"|grep test.ping|grep -v grep|while read psline;
    do
        seconds="$(echo "$psline"|awk '{print $2}')"
        pid="$(echo $psline|awk '{print $1}')"
        if [ "${seconds}" -gt "$((60*2))" ];then
            bs_log "Salt PING stalled, killing old salt call process: $pid"
            bs_log "$psline"
            kill -9 "${pid}"
            touch /tmp/bootsaltmode
        fi
    done
    if [ -f /tmp/bootsaltmode ];then
        restart_modes="${restart_modes} full"
        rm -f /tmp/bootsaltmode
    fi
    # ping masters if we are not already forcing restart
    if [ "x${alive_mode}" != "xrestart" ];then
        if [ "x${IS_SALT}" != "x" ];then
            resultping="$(salt_ping_test)"
            if [ "x${resultping}" != "x0" ];then
                restart_modes="${restart_modes} salt"
            fi
        fi
        if [ "x${IS_MASTERSALT}" != "x" ];then
            resultping="$(mastersalt_ping_test)"
            if [ "x${resultping}" != "x0" ];then
                restart_modes="${restart_modes} mastersalt"
            fi
        fi
    fi
    if [ "x$(echo "${restart_modes}"|grep -q full;echo ${?})" = "x0" ];then
        bs_log "Something went wrong with last restart, restarting old salt daemons"
        restart_daemons
    else
        for restart_mode in ${restart_modes};do
            if [ "x$(echo "${restart_mode}"|grep -v mastersalt|grep -q salt;echo ${?})" = "x0" ];then
                bs_log "Something went wrong with last restart, restarting old local salt daemons"
                restart_local_minions
                restart_local_masters
            fi
            if [ "x$(echo "${restart_mode}"|grep mastersalt|grep -q mastersalt;echo ${?})" = "x0" ];then
                bs_log "Something went wrong with last restart, restarting old master salt daemons"
                restart_local_mastersalt_masters
                restart_local_mastersalt_minions
            fi
        done
    fi
    # and finally, last try to start daemon if they are not present
    if [ "$(ps aux|grep boot-salt|grep -v grep|wc -l|sed -e "s/ //g")" -lt "4" ];then
        lazy_start_mastersalt_daemons
        lazy_start_salt_daemons
    fi
}

synchronize_code() {
    restart_modes=""
    # kill all stale synchronnise code jobs
    ps -eo pid,etimes,cmd|sort -n -k2|egrep "boot-salt.*synchronize-code"|grep -v grep|while read psline;
    do
        seconds="$(echo "$psline"|awk '{print $2}')"
        pid="$(echo $psline|awk '{print $1}')"
        if [ "${seconds}" -gt "200" ];then
            bs_log "something was wrong with last sync, killing old sync processes: $pid"
            bs_log "${psline}"
            kill -9 "${pid}"
        fi
    done
    setup_and_maybe_update_code
    if [ "x${QUIET}" = "x" ];then
        bs_log "Code updated"
    fi
    exit 0
}

set_dns() {
    if [ "${NICKNAME_FQDN}" != "x" ];then
        if [ "x$(cat /etc/hostname 2>/dev/null|sed -e "s/ //")" != "x$(echo "${HOST}"|sed -e "s/ //g")" ];then
            bs_log "Resetting hostname file to ${HOST}"
            echo "${HOST}" > /etc/hostname
        fi
        if [ "x$(domainname)" != "x$(echo "${DOMAINNAME}"|sed -e "s/ //g")" ];then
            bs_log "Resetting domainname to ${DOMAINNAME}"
            domainname "${DOMAINNAME}"
        fi
        if [ "x$(hostname)" != "x$(echo "${NICKNAME_FQDN}"|sed -e "s/ //g")" ];then
            bs_log "Resetting hostname to ${NICKNAME_FQDN}"
            hostname "${NICKNAME_FQDN}"
        fi
        if [ "x$(egrep -q "127.*${NICKNAME_FQDN}" /etc/hosts;echo ${?})" != "x0" ];then
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

cleanup_execlogs() {
    LOG_LIMIT="${LOG_LIMIT:-20}"
    # keep 20 local exec logs only
    for dir in "${SALT_MS}/.bootlogs" "${MASTERSALT_MS}/.bootlogs";do
        if [ -e "${dir}" ];then
            cd "${dir}"
            if [ "$(ls -1|wc -l|sed -e "s/ //")" -gt "${LOG_LIMIT}" ];then
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

postinstall() {
   if [ x${FORCE_IS_MASTERSALT_MASTER} = "no" ];then
         killall_local_mastersalt_masters
         rm -f /etc/init*/mastersalt-master*
    fi
    if [ x${FORCE_IS_SALT_MASTER} = "no" ];then
         killall_local_masters
         rm -f /etc/init*/salt-master*
    fi
    if [ "x${SALT_CLOUD}" != "x" ];then
        if [ "x${IS_SALT}" != "x" ];then
            lazy_start_salt_daemons
        fi
        if [ "x${IS_MASTERSALT}" != "x" ];then
           lazy_start_mastersalt_daemons
        fi
    fi
}

if [ "x${SALT_BOOT_AS_FUNCS}" = "x" ];then
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
    if [ x${SALT_BOOT_SYNC_CODE} != "x" ];then
        synchronize_code
    fi
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
        cleanup_old_installs
        setup_and_maybe_update_code
        handle_upgrades
        setup_virtualenv
        install_buildouts
        create_salt_skeleton
        install_mastersalt_env
        install_salt_env
        run_highstates
        maybe_install_projects
        maybe_run_tests
        postinstall
    fi
    exit 0
fi
# vim:set et sts=5 ts=4 tw=0:

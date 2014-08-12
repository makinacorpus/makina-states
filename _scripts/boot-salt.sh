#!/usr/bin/env bash
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

get_curgitpackid() {
    python << EOF
try:
    with open('${1}') as fic:
        print int(fic.read().strip())
except Exception:
    print 0
EOF
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
VALID_CHANGESETS=""
PATH="${PATH}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"
if [ -h "${THIS}" ];then
    THIS="$(readlink ${THIS})"
fi
THIS="$(get_abspath ${THIS})"
export PATH

is_container() {
    if cat -e /proc/1/cgroup 2>/dev/null|egrep -q 'docker|lxc';then
        echo "0"
    else
        echo "1"
    fi
}

filter_host_pids() {
    pids=""
    if [ "x$(is_container)" = "x0" ];then
        pids="${pids} $(echo "${@}")"
    else
        for pid in ${@};do
            if [ "x$(grep -q /lxc/ /proc/${pid}/cgroup 2>/dev/null;echo "${?}")" != "x0" ];then
                pids="${pids} $(echo "${pid}")"
            fi
         done
    fi
    echo "${pids}" | sed -e "s/\(^ \+\)\|\( \+$\)//g"
}

set_progs() {
    UNAME="${UNAME:-"$(uname | awk '{print tolower($1)}')"}"
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
    PS="$(which ps)"
    NC=$(which nc 2>/dev/null)
    NETCAT=$(which netcat 2>/dev/null)
    if [ ! -e "${NC}" ];then
        if [ -e "${NETCAT}" ];then
            NC=${NETCAT}
        fi
    fi
    export SED GETENT PERL PYTHON DIG NSLOOKUP PS NC
}

sanitize_changeset() {
    echo "${1}" | sed -e "s/changeset://g"
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

get_do_mastersalt() {
    ret="no"
    if [ "x${DO_MASTERSALT}" != "xno" ];then
        ret="y"
        if [ "x$(get_bootsalt_mode)" != "xmastersalt" ];then
            ret="no"
        fi
    fi
    echo "${ret}"
}

# X: connection failure
# 0: connection success
check_connectivity() {
    ip=${1}
    tempo="${3:-1}"
    port=${2}
    ret="0"
    if [ -e "${NC}" ];then
        while [ "x${tempo}" != "x0" ];do
            tempo="$((${tempo} - 1))"
            # one of
            # Connection to 127.0.0.1 4506 port [tcp/*] succeeded!
            # foo [127.0.0.1] 4506 (?) open
            ret=$(${NC} -w 5 -v -z ${ip} ${port} 2>&1|egrep -q "open$|Connection.*succeeded";echo ${?})
            if [ "x${ret}" = "x0" ];then
                break
            fi
            sleep 1
        done
    fi
    echo ${ret}
}

die_() {
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
    if [ "x${?}" = "x0" ] || [ "x${TRAVIS}" != "x" ];then
        return 0
    fi
    return 1
}

dns_resolve() {
    ahost="${1}"
    resolvers="hostsv4 hostsv6"
    res=""
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
    for resolver in ${resolvers};do
        if echo ${resolver} | grep -q hostsv4;then
            res=$(${GETENT} ahostsv4 ${ahost}|head -n1 2>/dev/null| awk '{ print $1 }')
        elif echo ${resolver} | grep -q hostsv6;then
            res=$(${GETENT} ahostsv6 ${ahost}|head -n1 2>/dev/null| awk '{ print $1 }')
        elif echo ${resolver} | grep -q dig;then
            res=$(${resolver} ${ahost} 2>/dev/null| awk '/^;; ANSWER SECTION:$/ { getline ; print $5 }')
        elif echo ${resolver} | grep -q nslookup;then
            res=$(${resolver} ${ahost} 2>/dev/null| awk '/^Address: / { print $2  }')
        elif echo ${resolver} | grep -q python;then
            res=$(${resolver} -c "import socket;print socket.gethostbyname('${ahost}')" 2>/dev/null)
        elif echo ${resolver} | grep -q perl;then
            res=$(${resolver} -e "use Socket;\$packed_ip=gethostbyname(\"${ahost}\");print inet_ntoa(\$packed_ip)")
        elif echo ${resolver} | grep -q getent;then
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

## set environment variables determining the underlying os
detect_os() {
    # make as a function to be copy/pasted as-is in multiple scripts
    set_progs
    UNAME="${UNAME:-"$(uname | awk '{print tolower($1)}')"}"
    DISTRIB_CODENAME=""
    DISTRIB_ID=""
    DISTRIB_BACKPORT=""
    if hash -r lsb_release >/dev/null 2>&1;then
        DISTRIB_ID=$(lsb_release -si)
        DISTRIB_CODENAME=$(lsb_release -sc)
        DISTRIB_RELEASE=$(lsb_release -sr)
    else
        echo "unespected case, no lsb_release"
        exit 1
    fi
    if [ "x${DISTRIB_ID}" = "xDebian" ];then
        DISTRIB_BACKPORT="${DISTRIB_CODENAME}-backports"
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
        bs_yellow_log "The installation will continue in ${1:-60} seconds"
        bs_yellow_log "unless you press enter to continue or C-c to abort"
        bs_yellow_log "-------------------  ????  -----------------------"
        read -t ${1:-60}
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

get_default_knob() {
    key="${1}"
    stored_param="$(get_conf ${key})"
    cli_param="${2}"
    default="${3:-}"
    if [ "x${cli_param}" != "x" ];then
        setting="${cli_param}"
    elif [ "x${stored_param}" != "x" ];then
        setting="${stored_param}"
    else
        setting="${default}"
    fi
    if [ "x${stored_param}" != "x${setting}" ];then
        store_conf ${key} "${setting}"
    fi
    echo "${setting}"
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

get_salt_url() {
    get_default_knob salt_url "${SALT_URL}" "https://github.com/makinacorpus/salt.git"
}

get_salt_branch() {
    get_default_knob salt_branch "${SALT_BRANCH}" "2015.8"
}

get_ms_url() {
    get_default_knob ms_url "${MAKINASTATES_URL}" "https://github.com/makinacorpus/makina-states.git"
}

get_local_mastersalt_mode() {
    get_default_knob local_mastersalt_mode "${FORCE_LOCAL_MASTERSALT_MODE}" "remote"
}

get_local_salt_mode() {
    get_default_knob local_salt_mode "${FORCE_LOCAL_SALT_MODE}" "masterless"
}

get_minion_id() {
    confdirs="${1:-"/etc/mastersalt /etc/salt"}"
    force="${3}"
    notfound=""
    for confdir in $confdirs;do
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
        if ! echo "${mmid}" | grep -q '\.';then
            mmid="${mmid}.${DEFAULT_DOMAINNAME}"
        fi
        if [ "x${mmid}" != "x" ];then
            break
        fi
    done
    echo $mmid
}

set_valid_upstreams() {
    if [ "x${SETTED_VALID_UPSTREAM}" != "x" ];then
        return
    fi
    if [ ! -e "$(which git 2>/dev/null)" ];then
        VALID_BRANCHES="master stable"
    fi
    if [ "x${VALID_BRANCHES}" = "x" ];then
        if [ "x${SALT_BOOT_LIGHT_VARS}" = "x" ];then
            VALID_BRANCHES="$(echo "$(git ls-remote "$(get_ms_url)"|grep "refs/heads"|awk -F/ '{print $3}'|grep -v HEAD)")"
        fi
        if [ -e "${SALT_MS}/.git/config" ];then
            SETTED_VALID_UPSTREAM="1"
            VALID_BRANCHES="${VALID_BRANCHES} $(echo $(cd "${SALT_MS}" && git branch| cut -c 3-))"
            VALID_CHANGESETS="${VALID_CHANGESETS} $(echo $(cd "${SALT_MS}" && git log --pretty=format:'%h %H'))"

        fi
        if [ -e "${MASTERSALT_MS}/.git/config" ];then
            SETTED_VALID_UPSTREAM="1"
            VALID_BRANCHES="${VALID_BRANCHES} $(echo $(cd "${MASTERSALT_MS}" && git branch| cut -c 3-))"
            VALID_CHANGESETS="${VALID_CHANGESETS} $(echo $(cd "${MASTERSALT_MS}" && git log --pretty=format:'%h %H'))"
        fi
    fi
    # remove \n
    VALID_BRANCHES=$(echo $(echo "${VALID_BRANCHES}"|tr -s "[:space:]" "\\n"|sort -u))
    VALID_CHANGESETS=$(echo $(echo "${VALID_CHANGESETS}"|tr -s "[:space:]" "\\n"|sort -u))
}

get_mastersalt() {
    local pmastersalt=""
    local mastersalt="${MASTERSALT:-}"
    # host running the mastersalt salt-master
    if [ "x${SALT_REATTACH}" != "x" ] && [ -e "${SALT_REATTACH_DIR}/minion" ];then
         mastersalt="$(egrep "^master:" "${SALT_REATTACH_DIR}"/minion 2>/dev/null|awk '{print $2}'|${SED} -e "s/ //")"
    fi

    if [ "x${mastersalt}" = "x" ] && [ "x${SALT_REATTACH}" = "x" ] && [ -e "${MASTERSALT_PILLAR}/mastersalt.sls" ];then
        pmastersalt="$(grep "master: " ${MASTERSALT_PILLAR}/mastersalt.sls |awk '{print $2}'|tail -n 1|${SED} -e "s/ //g")"
        if [ "x${pmastersalt}" != "x" ];then
            mastersalt="${pmastersalt}"
        fi
    fi
    if [ "x${mastersalt}" = "x" ];then
        for i in /etc/mastersalt/minion /etc/mastersalt/minion.d/00_global.conf;do
            if [ "x${mastersalt}" = "x" ] && [ -e "${i}" ];then
                pmastersalt="$(egrep "^master: " ${i} |awk '{print $2}'|tail -n 1|${SED} -e "s/ //g")"
                if [ "x${pmastersalt}" != "x" ];then
                    mastersalt="${pmastersalt}"
                    break
                fi
            fi
        done
    fi
    if [ "x${mastersalt}" = "x" ] && [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then
        mastersalt="localhost"
    fi
    echo "${mastersalt}"
}

validate_changeset() {
    set_valid_upstreams
    msb="${1}"
    ret=""
    # also add if we had a particular changeset saved in conf
    # remove
    if [ "x${msb}" != "x" ];then
        c="$(sanitize_changeset ${msb})"
        thistest="$(echo "${VALID_CHANGESETS}" "${VALID_BRANCHES}" | grep -q "${c}";echo "${?}")"
        if [ "x${thistest}" = "x0" ];then
            ret="${msb}"
        fi

    fi
    # if we pin a particular changeset make hat as a valid branch
    if [ "x${ret}" = "x" ];then
        for saltms in "${SALT_MS}" "${MASTERSALT_MS}";do
            if [ -e "${saltms}/.git" ];then
                thistest="$(cd "${saltms}" && git log "${msb}" 2>/dev/null 1>/dev/null;echo ${?})"
                if [ "x${thistest}" = "x0" ];then
                    ret="${msb}"
                    break
                fi
            fi
        done
    fi
    if [ "x${ret}" != "x" ];then
       echo "${ret}"
    fi
}

get_ms_branch() {
    set_valid_upstreams
    DEFAULT_MS_BRANCH="master"
    vmsb=""
    for msb in "${MS_BRANCH}" "$(get_conf branch)";do
        cmsb="$(validate_changeset ${msb})"
        if [ "x${cmsb}" != "x" ];then
            vmsb="${cmsb}"
            break
        fi
    done
    if [ "x${vmsb}" = "x" ];then
        vmsb="${DEFAULT_MS_BRANCH}"
    fi
    echo "${vmsb}"
}

get_bootsalt_mode() {
    bootsalt_mode="$(get_conf bootsalt_mode)"
    if [ "x${bootsalt_mode}" = "x" ];then
        if [ "x${IS_MASTERSALT}" != "x" ] || [ "${IS_MASTERSALT_MINION}" != "x" ];then
            bootsalt_mode="mastersalt"
        else
            bootsalt_mode="salt"
        fi
    fi
    echo "${bootsalt_mode}"
}

validate_nodetype() {
    n="${1}"
    if [ "x${n}" != "x" ];then
        if [ -e "${SALT_MS}" ];then
            saltms="${SALT_MS}"
        elif [ -e "${MASTERSALT_MS}" ];then
            saltms="${MASTERSALT_MS}"
        else
            saltms=""
        fi
        # at first we may have download just the bootsalt script, fallback on well known nodetypes
        if [ ! -e "${saltms}/nodetypes/${n}.sls" ];then
            # invalid nodetype, use default
            if ! echo "${n}" | egrep -q "devhost|dockercontainer|kvm|laptop|lxccontainer|server|scratch|travis|vagrantvm|vm";then
               n=""
            fi
        fi
    fi
    echo "${n}"
}

get_default_nodetype() {
    fallback_nt="server"
    if [ "x${TRAVIS}" != "x" ];then
        DEFAULT_NT="travis"
    elif [ "x$(is_container)" = "x0" ];then
        DEFAULT_NT="lxccontainer"
    else
        DEFAULT_NT="${fallback_nt}"
    fi
    echo "$(validate_nodetype ${DEFAULT_NT})"
}

get_salt_nodetype() {
    get_default_knob nodetype "$(validate_nodetype ${FORCE_SALT_NODETYPE})" "$(get_default_nodetype)"
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
    HOST="$(hostname -f)"
    DEFAULT_DOMAINNAME="${DEFAULT_DOMAINNAME:-local}"
    if [ $(hostname -f|sed -e "s/\./\.\n/g"|grep -c "\.") -ge 2 ];then
        HOST="$(hostname -f|$SED -re "s/([^.]+)\.(.*)/\1/g")"
        DEFAULT_DOMAINNAME="$(hostname -f|sed -re "s/[^.]+\.(.*)/\1/g")"
    fi
    HOST=$(echo ${HOST} | $SED "s/ //g")
    SALT_BOOT_LOCK_FILE="/tmp/boot_salt_sleep-$(get_full_chrono)"
    LAST_RETCODE_FILE="/tmp/boot_salt_rc-$(get_full_chrono)"
    QUIET=${QUIET:-}
    ROOT="${ROOT:-"/"}"
    CONF_ROOT="${CONF_ROOT:-"${ROOT}etc"}"
    ETC_INIT="${ETC_INIT:-"${CONF_ROOT}/init"}"
    ETC_SYSTEMD="${ETC_SYSTEMD:-"${CONF_ROOT}/systemd/system"}"
    CHRONO="$(get_chrono)"
    TRAVIS_DEBUG="${TRAVIS_DEBUG:-}"
    VENV_REBOOTSTRAP="${VENV_REBOOTSTRAP:-}"
    ONLY_BUILDOUT_REBOOTSTRAP="${ONLY_BUILDOUT_REBOOTSTRAP:-}"
    BUILDOUT_REBOOTSTRAP="${BUILDOUT_REBOOTSTRAP:-${VENV_REBOOTSTRAP}}"
    SALT_REBOOTSTRAP="${SALT_REBOOTSTRAP:-${VENV_REBOOTSTRAP}}"
    BASE_PACKAGES="python-software-properties curl python-virtualenv git rsync libzmq3-dev"
    BASE_PACKAGES="${BASE_PACKAGES} libmemcached-dev acl build-essential m4 libtool pkg-config autoconf gettext bzip2"
    BASE_PACKAGES="${BASE_PACKAGES} groff man-db automake libsigc++-2.0-dev tcl8.5 python-dev"
    BASE_PACKAGES="${BASE_PACKAGES} debconf-utils swig libssl-dev libgmp3-dev libffi-dev"
    DO_NODETYPE="${DO_NODETYPE:-"y"}"
    DO_SALT="${DO_SALT:-"y"}"
    DO_MASTERSALT="${DO_MASTERSALT:-"y"}"
    if [ "x$(get_do_mastersalt)" != "xy" ];then
        DO_MASTERSALT="no"
    fi
    if [ "x${DO_NODETYPE}" != "xy" ];then
        DO_NODETYPE="no"
    fi
    if [ "x${DO_SALT}" != "xy" ];then
        DO_SALT="no"
    fi
    BRANCH_PILLAR_ID="makina-states.salt.makina-states.rev"
    MAKINASTATES_TEST=${MAKINASTATES_TEST:-}
    SALT_BOOT_INITIAL_HIGHSTATE="${SALT_BOOT_INITIAL_HIGHSTATE:-}"
    IS_SALT_UPGRADING="${IS_SALT_UPGRADING:-}"
    IS_SALT="${IS_SALT:-y}"
    NO_MS_VENV_CACHE="${NO_MS_VENV_CACHE:-}"
    IS_SALT_MASTER="${IS_SALT_MASTER:-y}"
    IS_SALT_MINION="${IS_SALT_MINION:-y}"
    IS_MASTERSALT="${IS_MASTERSALT:-}"
    IS_MASTERSALT_MASTER="${IS_MASTERSALT_MASTER:-}"
    IS_MASTERSALT_MINION="${IS_MASTERSALT_MINION:-}"
    PREFIX="${PREFIX:-${ROOT}srv}"
    BIN_DIR="${BIN_DIR:-${ROOT}usr/bin}"
    SALT_ROOT="${SALT_ROOT:-$PREFIX/salt}"
    MASTERSALT_ROOT="${MASTERSALT_ROOT:-$PREFIX/mastersalt}"
    SALT_MS="${SALT_ROOT}/makina-states"
    SALT_PILLAR="${SALT_PILLAR:-$PREFIX/pillar}"
    SALT_BOOT_SYNC_CODE="${SALT_BOOT_SYNC_CODE:-}"
    SALT_BOOT_SYNC_DEPS="${SALT_BOOT_SYNC_DEPS:-onlysync}"
    SALT_BOOT_NOCONFIRM="${SALT_BOOT_NOCONFIRM:-}"
    SALT_BOOT_ONLY_PREREQS="${SALT_BOOT_ONLY_PREREQS}"
    SALT_BOOT_ONLY_INSTALL_SALT="${SALT_BOOT_ONLY_INSTALL_SALT}"
    MASTERSALT_PILLAR="${MASTERSALT_PILLAR:-$PREFIX/mastersalt-pillar}"
    MASTERSALT_MS="${MASTERSALT_ROOT}/makina-states"
    TMPDIR="${TMPDIR:-"/tmp"}"
    VENV_PATH="${VENV_PATH:-"/salt-venv"}"
    EGGS_GIT_DIRS="salt salttesting"
    PIP_CACHE="${VENV_PATH}/cache"
    SALT_VENV_PATH="${VENV_PATH}/salt"
    MASTERSALT_VENV_PATH="${VENV_PATH}/mastersalt"
    CONF_PREFIX="${CONF_PREFIX:-"${CONF_ROOT}/salt"}"
    MCONF_PREFIX="${MCONF_PREFIX:-"${CONF_ROOT}/mastersalt"}"
    # global installation marker
    SALT_BOOT_NOW_INSTALLED=""
    # the current mastersalt.makinacorpus.net hostname
    # base sls bootstrap
    bootstrap_pref="makina-states.bootstraps"
    bootstrap_nodetypes_pref="${bootstrap_pref}.nodetypes"
    bootstrap_controllers_pref="${bootstrap_pref}.controllers"

    # nodetypes (calculed now in get_salt_nodetype) and controllers sls
    SALT_MASTER_CONTROLLER_DEFAULT="salt_master"
    SALT_MASTER_CONTROLLER_INPUTED="${SALT_MASTER_CONTROLLER}"
    SALT_MASTER_CONTROLLER="${SALT_MASTER_CONTROLLER:-$SALT_MASTER_CONTROLLER_DEFAULT}"
    SALT_MINION_CONTROLLER_DEFAULT="salt_minion"
    SALT_MINION_CONTROLLER_INPUTED="${SALT_MINION_CONTROLLER}"
    SALT_MINION_CONTROLLER="${SALT_MINION_CONTROLLER:-$SALT_MINION_CONTROLLER_DEFAULT}"
    DO_PIP="${DO_PIP:-}"
    DO_MS_PIP="${DO_MS_PIP:-}"
    SALT_LIGHT_INSTALL=""
    HOST="$(get_minion_id|$SED -re "s/([^.]+)\.(.*)/\1/g")"
    DOMAINNAME="$(get_minion_id|${SED} -e "s/^[^.]*\.//")"
    DOMAINNAME="${DOMAINNAME:-${DEFAULT_DOMAINNAME}}"
    DOMAINNAME=$(echo ${DOMAINNAME} | $SED "s/ //g")
    if [ "x${DOMAINNAME}" = "x" ];then
        DOMAINNAME="local"
    fi
    NICKNAME_FQDN="${HOST}.${DOMAINNAME}"
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
        || [ -f "${ETC_SYSTEMD}/salt-master.service" ]\
        || [ -e "${ETC_INIT}.d/salt-master" ]\
        || [ "x${IS_SALT_MASTER}" != "x" ];then
        IS_SALT="y"
        IS_SALT_MASTER="y"
        IS_SALT_MINION="y"
    fi
    if [ -e "${ETC_INIT}/salt-minion.conf" ]\
        || [ -f "${ETC_SYSTEMD}/salt-minion.service" ]\
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
            || [ -f "${ETC_SYSTEMD}/mastersalt-master.service" ]\
            || [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            MASTERSALT_INIT_MASTER_PRESENT="y"
            MASTERSALT_INIT_PRESENT="y"
        fi
        if [ -e "${ETC_INIT}.d/mastersalt-minion" ]\
            || [ -e "${ETC_INIT}/mastersalt-minion.conf" ]\
            || [ -f "${ETC_SYSTEMD}/mastersalt-minion.service" ]\
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
    MASTERSALT_MASTER_CONTROLLER_DEFAULT="mastersalt_master"
    MASTERSALT_MASTER_CONTROLLER_INPUTED="${MASTERSALT_MASTER_CONTROLLER}"
    MASTERSALT_MASTER_CONTROLLER="${MASTERSALT_MASTER_CONTROLLER:-${MASTERSALT_MASTER_CONTROLLER_DEFAULT}}"
    MASTERSALT_MINION_CONTROLLER_DEFAULT="mastersalt_minion"
    MASTERSALT_MINION_CONTROLLER_INPUTED="${MASTERSALT_MINION_CONTROLLER}"
    MASTERSALT_MINION_CONTROLLER="${MASTERSALT_MINION_CONTROLLER:-${MASTERSALT_MINION_CONTROLLER_DEFAULT}}"
    # mastersalt variables
    if [ "x${IS_MASTERSALT}" != "x" ];then
        store_conf bootsalt_mode mastersalt
    else
        store_conf bootsalt_mode salt
    fi
    if [ "x${IS_MASTERSALT}" != "x" ];then
        if [ "x${SALT_REATTACH}" != "x" ] && [ -e "${SALT_REATTACH_DIR}/minion" ];then
             MASTERSALT_MASTER_DNS="$(get_mastersalt)"
             MASTERSALT_MASTER_IP="$(get_mastersalt)"
             MASTERSALT_MASTER_PORT="$(egrep "^master_port:" "${SALT_REATTACH_DIR}"/minion|awk '{print $2}'|${SED} -e "s/ //")"
        fi
        if [ "x$(get_mastersalt)" = "x" ] && [ "x${IS_MASTERSALT_MASTER}" ];then
            MASTERSALT="${NICKNAME_FQDN}"
            MASTERSALT_MASTER_DNS="${NICKNAME_FQDN}"
        fi

        MASTERSALT_MASTER_DNS="${MASTERSALT_MASTER_DNS:-$(get_mastersalt)}"
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
    set_valid_upstreams
    if [ "x${MS_BRANCH}" != "x" ] && [ "x$(validate_changeset ${MS_BRANCH})" = "x" ];then
        bs_yellow_log "Valid branches: $(echo ${VALID_BRANCHES})"
        die "Please provide a valid \$MS_BRANCH (or -b \$branch) (inputed: "$(get_ms_branch)")"
    fi
    if [ "x$(get_salt_nodetype)" = "x" ];then
        bs_yellow_log "Valid nodetypes $(echo $(ls "${SALT_MS}/nodetypes"|"${SED}" -e "s/.sls//"))"
        die "Please provide a valid nodetype (inputed: "$(get_salt_nodetype)")"
    fi

    # just tell to bootstrap and run highstates
    SALT_BOOT_SKIP_CHECKOUTS="${SALT_BOOT_SKIP_CHECKOUTS:-}"
    if [ "x${IS_SALT_UPGRADING}" != "x" ];then
        SALT_BOOT_SKIP_HIGHSTATES=""
        MASTERSALT_BOOT_SKIP_HIGHSTATE=""
        SALT_BOOT_SKIP_CHECKOUTS="${FORCE_SALT_BOOT_SKIP_CHECKOUTS:-}"
        SALT_REBOOTSTRAP="y"
        DO_PIP="y"
        DO_MS_PIP="y"
        BUILDOUT_REBOOTSTRAP="y"
    fi
    if [ "x${QUIET}" = "x" ];then
        QUIET_GIT=""
    else
        QUIET_GIT="-q"
    fi

    # try to get a released version of the virtualenv to speed up installs
    VENV_URL="${VENV_URL:-"https://github.com/makinacorpus/makina-states/releases/download/attachedfiles/virtualenv-makina-states-${DISTRIB_ID}-${DISTRIB_CODENAME}-stable.tar.xz"}"
    declare -A VENV_URLS_MD5
    VENV_URLS_MD5[ahttps://github.com/makinacorpus/makina-states/releases/download/attachedfiles/virtualenv-makina-states-ubuntu-vivid-stable.tar.xz]="940c8d19e6b7d25dffb091634ddf629a"
    VENV_URLS_MD5[ahttps://github.com/makinacorpus/makina-states/releases/download/attachedfiles/virtualenv-makina-states-ubuntu-trusty-stable.tar.xz]="4a8a83c02846770b4686b4b01b9b8e18"
    VENV_MD5=${VENV_MD5:-${VENV_URLS_MD5[${VENV_URL}]}}
    # export variables to support a restart

    export MS_BRANCH="$(get_ms_branch)"
    export VENV_URL VENV_MD5 VENV_URLS_MD5 NO_MS_VENV_CACHE
    export SALT_BOOT_ONLY_PREREQS SALT_BOOT_ONLY_INSTALL_SALT
    export BS_MS_ASSOCIATION_RESTART_MINION BS_MS_ASSOCIATION_RESTART_MASTER
    export BS_ASSOCIATION_RESTART_MASTER BS_ASSOCIATION_RESTART_MINION
    export DO_PIP DO_MS_PIP DO_MASTERSALT DO_SALT DO_REFRESH_MODULES DO_NODETYPE
    export FORCE_SALT_BOOT_SKIP_CHECKOUTS
    export ONLY_BUILDOUT_REBOOTSTRAP
    export EGGS_GIT_DIRS
    export TRAVIS_DEBUG SALT_BOOT_LIGHT_VARS TRAVIS
    export IS_SALT_UPGRADING SALT_BOOT_SYNC_CODE SALT_BOOT_INITIAL_HIGHSTATE SALT_BOOT_SYNC_DEPS
    export SALT_REBOOTSTRAP BUILDOUT_REBOOTSTRAP VENV_REBOOTSTRAP
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
    export ROOT PREFIX ETC_INIT ETC_SYSTEMD
    export VENV_PATH CONF_ROOT
    export SALT_VENV_PATH PIP_CACHE MASTERSALT_VENV_PATH
    export MCONF_PREFIX CONF_PREFIX
    #
    export FORCE_SALT_NODETYPE
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
    export TRAVIS
    export FORCE_GIT_PACK ONLY_GIT_PACK

}

check_py_modules() {
    # test if salt binaries are there & working
    kind="${1:-"salt"}"
    bin="${VENV_PATH}/${kind}/bin/python"
    "${bin}" << EOF
import dns
import docker
import salt
import tornado.ioloop
import chardet
import OpenSSL
import urllib3
import ipaddr
import ipwhois
import pyasn1
from distutils.version import LooseVersion
OpenSSL_version = LooseVersion(OpenSSL.__dict__.get('__version__', '0.0'))
if OpenSSL_version <= LooseVersion('0.15'):
    raise ValueError('trigger upgrade pyopenssl')
# futures
import concurrent
EOF
    return ${?}
}

is_salt_bins_in_place() {
    # test if salt binaries are there & working
    ret=0
    kind="${1:-"salt"}"
    bins="salt salt-api salt-call salt-cloud salt-cp salt-jenkins-build"
    bins="${bins} salt-key salt-master salt-minion salt-run salt-ssh"
    bins="${bins} salt-syndic salt-unity"
    if [ "x${DO_PIP}" = "x" ];then
        for i in ${bins};do
            bin="${VENV_PATH}/${kind}/bin/${i}"
            if [ ! -e "${bin}" ];then
                ret=1
                break
            else
                py="${VENV_PATH}/${kind}/bin/python"
                fic="$(mktemp)"
                # strip the exec part of the pip wrapper, but let the code import
                # to maybe throw an import error signaling a broken pip install
                $SED -e "s/exec(compile(\(.*\)))/compile(\1)/g" "${bin}" > "${fic}"
                "${py}" "${fic}" 1>/dev/null 2>/dev/null
                if [ "x${?}" != "x0" ];then
                    ret=1
                    break
                fi
                rm -f "${fic}"
            fi
        done
    fi
    return ${ret}
}

# --------- PROGRAM START

mastersalt_processes() {
    ps aux|grep mastersalt
}

recap_(){
    need_confirm="${1}"
    debug="${2:-$SALT_BOOT_DEBUG}"
    bs_yellow_log "----------------------------------------------------------"
    bs_yellow_log " MAKINA-STATES BOOTSTRAPPER (@$(get_ms_branch)) FOR $DISTRIB_ID"
    bs_yellow_log "   - ${THIS} [--help] [--long-help]"
    bs_yellow_log " Those informations have been written to:"
    bs_yellow_log "   - ${TMPDIR}/boot_salt_top"
    bs_yellow_log "----------------------------------------------------------"
    if [ "x$(get_do_mastersalt)" = "xno" ];then
        bs_yellow_log "mastersalt skipped"
    fi
    if [ "x${DO_SALT}" = "xno" ];then
        bs_yellow_log "salt skipped"
    fi
    bs_yellow_log "HOST variables:"
    bs_yellow_log "---------------"
    bs_log "  Minion Id: $(get_minion_id)"
    bs_log "HOST/DOMAIN: ${HOST}/${DOMAINNAME}"
    bs_log "DATE: ${CHRONO}"
    bs_log "LOCAL_SALT_MODE: $(get_local_salt_mode)"
    if [ "x$(get_do_mastersalt)" != "xno" ];then
        bs_log "LOCAL_MASTERSALT_MODE: $(get_local_mastersalt_mode)"
    fi
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
        bs_log "ROOT: ${ROOT}"
        bs_log "PREFIX: ${PREFIX}"
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
            bs_log "SALT_MASTER_DNS: ${SALT_MASTER_DNS}"
            bs_log "SALT_MASTER_PORT: ${SALT_MASTER_PORT}"
            bs_log "SALT_MINION_IP: ${SALT_MINION_IP}"
            bs_log "SALT_MINION_ID: ${SALT_MINION_ID}"
        fi
        if [ "x${debug}" != "x" ];then
            bs_log "SALT_MASTER_PUBLISH_PORT: ${SALT_MASTER_PUBLISH_PORT}"
            bs_log "salt_bootstrap_nodetype: ${salt_bootstrap_nodetype}"
            if [ "x${IS_SALT_MASTER}" != "x" ];then
                bs_log "salt_bootstrap_master: ${salt_bootstrap_master}"
                bs_log "SALT_MASTER_CONTROLLER: ${SALT_MASTER_CONTROLLER}"
                debug_msg "SALT_MASTER_CONTROLLER_INPUTED: ${SALT_MASTER_CONTROLLER_INPUTED}"
            fi
            if [ "x${IS_SALT_MINION}" != "x" ];then
                bs_log "salt_bootstrap_minion: ${salt_bootstrap_minion}"
                bs_log "SALT_MINION_CONTROLLER: ${SALT_MINION_CONTROLLER}"
                debug_msg "SALT_MINION_CONTROLLER_INPUTED: ${SALT_MINION_CONTROLLER_INPUTED}}"
            fi
        fi
    fi
    if [ "x${IS_MASTERSALT}" != "x" ];then
        bs_yellow_log "---------------------"
        bs_yellow_log "MASTERSALT variables:"
        bs_yellow_log "---------------------"
        bs_log "MASTERSALT ROOT | PILLAR: ${MASTERSALT_ROOT} | ${MASTERSALT_PILLAR}"
        bs_log "MASTERSALT: $(get_mastersalt)"
        if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            bs_log "MASTERSALT_MASTER_IP: ${MASTERSALT_MASTER_IP}"
            bs_log "MASTERSALT_MASTER_PUBLISH_PORT ${MASTERSALT_MASTER_PUBLISH_PORT}"
        fi
        if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
            bs_log "MASTERSALT_MASTER_PORT: ${MASTERSALT_MASTER_PORT}"
            bs_log "MASTERSALT_MINION_IP: ${MASTERSALT_MINION_IP}"
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
    if ! dpkg-query -s ${@} 2>/dev/null|egrep "^Status:"|grep -q installed;then
        return 1
    fi
}

lazy_apt_get_install() {
    MS_WITH_PKGMGR_UPDATE=${MS_WITH_PKGMGR_UPDATE:-}
    to_install=""
    for i in ${@};do
         if ! is_apt_installed ${i};then
             to_install="${to_install} ${i}"
         fi
    done
    if [ "x${to_install}" != "x" ];then
        bs_log "Installing ${to_install}"
        if [ "x${MS_WITH_PKGMGR_UPDATE}" != "x" ];then
            apt-get update
        fi
        apt-get install -y --force-yes ${to_install}
    fi
}

setup_backports() {
    # on ubuntu enable backports (saucy) release repos, & on debian just backport
    # saucy is now on archives !
    if [ "x${DISTRIB_BACKPORT}" != "x" ] && greq -vq "${DISTRIB_BACKPORT}" ${CONF_ROOT}/etc/apt/sources.list;then
        bs_log "Activating backport from ${DISTRIB_BACKPORT} to ${DISTRIB_CODENAME}"
        cp  ${CONF_ROOT}/apt/sources.list "${CONF_ROOT}/apt/sources.list.${CHRONO}.sav"
        "${SED}" "/^deb.*${DISTRIB_BACKPORT}/d" -i ${CONF_ROOT}/apt/sources.list
        echo "# backport added by boot-salt">/tmp/aptsrc
        egrep "^deb.* ${DISTRIB_CODENAME} " ${CONF_ROOT}/apt/sources.list | \
            "${SED}" -i -e "s/${DISTRIB_CODENAME}/${DISTRIB_BACKPORT}/g" \
            > /tmp/aptsrc${CHRONO}
        cat /tmp/aptsrc${CHRONO} >> ${CONF_ROOT}/apt/sources.list
        rm -f /tmp/aptsrc${CHRONO}
    fi

}

teardown_backports() {
    # deactivated, too much risk
    : noop
}

install_prerequisites() {
    if [ "x${QUIET}" = "x" ];then
        bs_log "Check package dependencies"
    fi
    MS_WITH_PKGMGR_UPDATE="y" lazy_apt_get_install ${BASE_PACKAGES} \
        || die " [bs] Failed install rerequisites"
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
    echo "${LOCAL}"
}

get_mastersaltcall_args() {
    if [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then
        LOCAL="--local"
    fi
    echo "${LOCAL}"
}

salt_call_wrapper_() {
    last_salt_retcode=-1
    contextual_ms=${1};shift
    saltargs=" --retcode-passthrough"
    if [ "x${SALT_BOOT_DEBUG}" != "x" ];then
        saltargs="${saltargs} -l${SALT_BOOT_DEBUG_LEVEL}"
    else
        saltargs="${saltargs} -linfo"
    fi
    if [ "x$(get_salt_nodetype)" = "xtravis" ];then
        touch /tmp/travisrun
        ( while [ -f /tmp/travisrun ];do sleep 15;echo "keep me open";sleep 45;done; )&
    fi
    bs_log "Calling:"
    echo ""\
        "${contextual_ms}/bin/python ${contextual_ms}/mc_states/saltcaller.py" \
        " --validate-states --no-display-ret --use-vt -v --executable" \
        " ${contextual_ms}/bin/salt-call ${saltargs} ${@}"
    "${contextual_ms}/bin/python" "${contextual_ms}/mc_states/saltcaller.py" \
        --validate-states --no-display-ret --use-vt -v --executable \
        "${contextual_ms}/bin/salt-call" ${saltargs} ${@}
    last_salt_retcode=${?}
    if [ "x$(get_salt_nodetype)" = "xtravis" ];then
        rm -f /tmp/travisrun
    fi
    return ${last_salt_retcode}
}

salt_call_wrapper() {
    salt_call_wrapper_ "${SALT_MS}" $(get_saltcall_args) ${@}
}

mastersalt_call_wrapper() {
    salt_call_wrapper_ "${MASTERSALT_MS}" $(get_mastersaltcall_args) -c ${MCONF_PREFIX} ${@}
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
    return
    if [ "x$(get_salt_nodetype)" = "xtravis" ] && [ "x${TRAVIS_DEBUG}" != "x" ];then
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
    if [ "x${DO_SALT}" != "xno" ] && [ "x${IS_SALT}" != "x" ];then
        SALT_MSS="${SALT_MSS} ${SALT_MS}"
    fi
    if  [ "x$(get_do_mastersalt)" != "xno" ] && [ "x${IS_MASTERSALT}" != "x" ];then
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

validadate_git_repo() {
    ret="1"
    for i in branches config HEAD index info objects refs;do
        if [ ! -e "${1}/${i}" ];then
            ret=""
        fi
    done
    echo "${ret}"
}

get_valid_git_repo() {
    repo="${1}"
    ret=""
    if [ "x${repo}" = "x" ];then
        repo="${PWD}"
    fi
    if [ "x$(validadate_git_repo "${repo}/.git")" = "x1" ];then
        ret="${repo}/.git"
    elif [ "x$(validadate_git_repo "${repo}")" = "x1" ];then
        ret="${repo}"
    fi
    echo "${ret}"
}

get_pack_marker() {
     gmarker="$(get_valid_git_repo "${@}")/curgitpackid"
     if [ "x${gmarker}" != "x/curgitpackid" ];then
         echo "${gmarker}"
     fi
}

get_pack_marker_value() {
    marker=$(get_pack_marker "${@}")
    if [ "x${marker}" != "x" ];then
        echo "$(get_curgitpackid "${marker}")"
    else
        echo -1
    fi
}

increment_gitpack_id() {
    repo="$(get_valid_git_repo "${@}")"
    if [ "x${repo}" != "x" ];then
        marker="$(get_pack_marker "${repo}")"
        echo "$(( $(get_pack_marker_value "${repo}") + 1 ))" > "${marker}"
    fi
}

git_pack_dir() {
    f="${1}"
    cd "${f}/.."
    # pack each 10th call
    git_counter="$(($(get_pack_marker_value) % 10))"
    if [ "x${git_counter}" = "x0" ];then
        bs_log "Git packing ${f}"
        git prune || /bin/true
        git gc --aggressive || /bin/true
    else
        bs_log "Git packing ${f} skipped (${git_counter}/10)"
    fi
    if [ "x${?}" = "x0" ];then
        increment_gitpack_id
    fi
}

git_pack() {
    bs_log "Maybe packing git repositories"
    # pack git repositories in salt scope
    find\
        "${SALT_VENV_PATH}/src" \
        "${SALT_ROOT}"\
        "${MASTERSALT_ROOT}"\
        "${SALT_PILLAR}"\
        "${MASTERSALT_PILLAR}"\
        -name .git -type d|while read f;do
            git_pack_dir "${f}"
    done
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
    minion_keys="$(find "${CONF_PREFIX}/pki/master/"{minions_pre,minions} -type f 2>/dev/null|wc -l|${SED} -e "s/ //g")"
    if ! test_online;then
        if [ ! -e "${CONF_PREFIX}" ]\
            || [ "x${minion_keys}" = "x0" ]\
            || [ ! -e "${SALT_MS}/src/salt" ]\
            || [ ! -e "${SALT_MS}/bin/salt-call" ]\
            || [ ! -e "${SALT_MS}/bin/salt" ];then
            bs_log "Offline mode and installation not enougthly completed, bailing out"
            exit 1
        fi
    fi
    if [ "x${SALT_BOOT_IN_RESTART}" = "x" ] && test_online;then
        skip_co="${SALT_BOOT_SKIP_CHECKOUTS}"
        if [ "x$(is_basedirs_there)" = "x" ];then
            skip_co=""
        fi
        if [ "x${skip_co}" = "x" ];then
            if [ "x${QUIET}" = "x" ];then
                bs_yellow_log "If you want to skip checkouts, next time do export FORCE_SALT_BOOT_SKIP_CHECKOUTS=y"
            fi
            for ms in ${SALT_MSS};do
                if [ ! -d "${ms}/.git" ];then
                        remote="remotes/origin/"
                        branch_pref=""
                        ms_branch="$(get_ms_branch)"
                        thistest="$(echo "${ms_branch}" | grep -q "changeset:";echo "${?}")"
                        if [ "x${thistest}" = "x0" ];then
                            ms_branch="$(sanitize_changeset "${ms_branch}")"
                            remote=""
                            branch_pref="changeset_"
                        fi
                        git clone ${QUIET_GIT} "$(get_ms_url)" "${ms}" &&\
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
                cd "${ms}"
                if [ ! -e src ];then
                    venv_path="$(get_venv_path ${ms})"
                    create_venv_dirs "${venv_path}"
                    ln -sf "${venv_path}/src" "${ms}/src"
                fi
                if [ ! -e src ];then
                    die " [bs] pb with linking venv in ${ms}"
                fi
                if [ -d src ] && [ ! -h  src ];then
                    die " [bs] pb with linking venv in ${ms} (2)"
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
                    if [ -e "${i}/.git" ]\
                        && [ "x${FORCE_SALT_BOOT_SKIP_CHECKOUTS}" = "x" ]\
                        && [ "x${do_update}" != "x" ];then
                        "${SED}" -i -e "s/filemode =.*/filemode=false/g" "${i}/.git/config" 2>/dev/null
                        remote="remotes/origin/"
                        co_branch="master"
                        pref=""
                        if [ "x${i}" = "x${ms}" ];then
                            co_branch="$(get_ms_branch)"
                            thistest="$(echo "${co_branch}" | grep -q "changeset:";echo "${?}")"
                            if [ "x${thistest}" = "x0" ];then
                                co_branch="$(sanitize_changeset "${co_branch}")"
                                pref="changeset:"
                                is_changeset="1"
                                branch_pref="changeset_"
                                remote=""
                            fi
                        fi
                        if  [ "x${i}" = "x${ms}/src/salttesting" ]\
                         || [ "x${i}" = "x${ms}/src/SaltTesting" ];then
                            co_branch="develop"
                        fi
                        if [ "x${i}" = "x${ms}/src/salt" ];then
                            co_branch="$(get_salt_branch)"
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
                                    [ "x${i}" = "x${ms}/src/SaltTesting" ] \
                                    || [ "x${i}" = "x${ms}/src/salttesting" ] \
                                    || [ "x${i}" = "x${ms}/src/docker-py" ] \
                                ;then
                                    git reset ${QUIET_GIT} --hard origin/${co_branch}
                                else
                                    git merge ${QUIET_GIT} --ff-only origin/${co_branch}
                                fi
                                SALT_BOOT_NEEDS_RESTART=1
                            fi
                        fi
                        if [ "x${?}" = "x0" ];then
                            increment_gitpack_id
                            if [ "x${QUIET}" = "x" ];then
                                bs_yellow_log "Downloaded/updated ${i}"
                            fi
                        else
                            die "Failed to download/update ${i}"
                        fi
                        if [ "x${i}" = "x${ms}" ];then
                            store_conf branch "${pref}${co_branch}"
                            for pillardir in "${SALT_PILLAR}" "${MASTERSALT_PILLAR}";do
                                if [ -e "${pillardir}" ];then
                                    find "${pillardir}" -type f | while read i;do
                                        sed -i -re "s/makina-states.rev: .*/makina-states.rev: ${co_branch}/g" "${i}"
                                    done
                                fi
                            done
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

service_activated() {
    local activated=""
    local s="${1}"
    hassysd="$(systemctl list-unit-files --type=service 2>/dev/null| egrep -q "^${s}.service.*enabled">/dev/null;echo ${?})"
    if [ "x$(grep -q manual /etc/init/${s}.override 2>/dev/null)" != "x0" ] || [ "x${hassysd}" = "x0" ];then
        activated="y"
    fi
    echo "${activated}"
}

service_exists() {
    local sexists=""
    local s="${1}"
    hassysd="$(systemctl list-unit-files --type=service 2>/dev/null| egrep -q ^${s}.service >/dev/null;echo ${?})"
    if [ -e "/etc/init/${s}.conf" ] || [ -e "/etc/init.d/${s}" ] || [ "x${hassysd}" = "x0" ];then
        sexists="y"
    fi
    echo "${sexists}"
}

service_() {
    local s="${1}"
    shift
    if [ "x$(service_activated ${s})" = "xy" ] && [ "x$(service_exists ${s})" = "xy" ];then
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

download_file() {
    url="${1}"
    dest="${2}"
    refmd5="${3}"
    bs_log "Downloading & extracting ${url}"
    curl -Lfk "${url}" > "${dest}"
    if [ "x${?}" != "x0" ];then
        bs_log "download error"
    else
        md5="$(md5sum "${dest}"|awk '{print $1}')"
        if [ "x${refmd5}" != "x" ];then
            if [ "x${refmd5}" != "x${md5}" ];then
                bs_log "MD5 verification failed ( ${md5} != ${refmd5})"
                return 1
            fi
        fi
        bs_log "download complete"
    fi

}

setup_virtualenvs() {
    if [ ! -e "${VENV_PATH}/salt/bin/salt" ];then
        tmparc="${TMPDIR:-/tmp}/salt.tar.xz"
        # only download if exists
        if [ "x${NO_MS_VENV_CACHE}" != "x" ];then
            bs_log "Warn: virtualenv cache forced-off, will rebuild"
        elif curl -kfI ${VENV_URL} >/dev/null 2>&1;then
            if ! download_file "${VENV_URL}" "${tmparc}" "${VENV_MD5}";then
                bs_log "Archive error, aborting"
                exit 1
            fi
            tar xJf "${tmparc}" -C /
            if [ "x${?}" != "x0" ];then
                bs_log "extract error"
            else
                bs_log "extract complete"
            fi
            rm -f "${tmparc}"
        else
            bs_log "Warn: virtualenv cache archive not found, will rebuild"
        fi
    fi
    if [ "x${DO_SALT}" != "xno" ];then
        setup_virtualenv "${SALT_VENV_PATH}"
    fi
    if [ "x$(get_do_mastersalt)" != "xno" ];then
        if [ "x${IS_MASTERSALT_MINION}" != "x" ] || [ "x${IS_MASTERSALT}" != "x" ];then
            setup_virtualenv "${MASTERSALT_VENV_PATH}"
        fi
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
        if [ ! -e "${PIP_CACHE}" ];then
            mkdir -p "${PIP_CACHE}"
        fi
        if [ ! -e "${venv_path}" ];then
            mkdir -p "${venv_path}"
        fi
        virtualenv --system-site-packages --unzip-setuptools ${venv_path} &&\
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
    create_venv_dirs "${venv_path}"
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
    skind="salt"
    if [ "x${venv_path}" = "x${MASTERSALT_VENV_PATH}" ];then
        skind="mastersalt"
    fi
    if is_salt_bins_in_place ${skind} && check_py_modules ${skind};then
        bs_log "Pip install in place for $skind"
    else
        bs_log "Python install incomplete for $skind"
        if pip --help | grep -q download-cache;then
            copt="--download-cache"
        else
            copt="--cache-dir"
        fi
        pip install -U $copt "${PIP_CACHE}" -r requirements/requirements.txt
        die_in_error "requirements/requirements.txt doesnt install"
        if [ "x${install_git}" != "x" ];then
            pip install -U $copt "${PIP_CACHE}" --no-deps -e "git+$(get_salt_url)@$(get_salt_branch)#egg=salt"
            die_in_error "salt develop doesnt install"
            pip install -U $copt "${PIP_CACHE}" --no-deps -r requirements/git_salt_requirements.txt
            die_in_error "requirements/git_salt_requirements.txt doesnt install"
        else
            cwd="${PWD}"
            for i in $EGGS_GIT_DIRS;do
                if [ -e "src/${i}/.git/config" ];then
                    cd "src/${i}"
                    pip install --no-deps -e .
                fi
                cd "${cwd}"
            done
        fi
        pip install --no-deps -e .
    fi
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

create_venv_dirs() {
    venv_path="${1:-${venv_path}}"
    if [ ! -e "${venv_path}/src" ];then
        mkdir -p "${venv_path}/src"
    fi
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
            if [ "x$(readlink ${where}/${i})" = "x${vpath}/${i}" ];then
                do_link=""
            else
                rm -v "${where}/${i}"
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
    killall_local_mastersalt_masters
    killall_local_mastersalt_minions
    killall_local_minions
    killall_local_masters
}

has_sshd() {
    if which sshd >/dev/null 2>&1;then
        return 0
    fi
    for i in /usr /usr/local /usr;do
        for j in sbin bin;do
            if [ -x "${i}/${j}/sshd" ];then
                return 0
            fi
        done
    done
    return 1
}

regenerate_openssh_keys() {
    if has_sshd;then
        bs_log "Regenerating sshd server keys"
        find /etc/ssh/ssh_host_* -type f 2>/dev/null|while read f;do rm -vf "${f}";done
        "${SALT_MS}/files/usr/bin/reset-host.py" --reset-sshd_keys --origin $(hostname -f)
    fi
}

check_ssh_keys() {
    ssh_gen_keys="1"
    for suf in "" "_key";do
        for i in dsa ecdsa ed25519 rsa;do
            key="/etc/ssh/ssh_host_${i}${suf}"
            c="${key}.pub"
            if [ -e "${c}" ] && [ -e "${key}" ];then
                # key exists, do not regen
                ssh_gen_keys=""
                break
            fi
        done
    done
    if [ "x${ssh_gen_keys}" != "x" ];then
        regenerate_openssh_keys
    fi
}

get_yaml_value() {
    gyaml_param="${1}"
    shift
    egrep -h "^${gyaml_param}: " ${@} 2>/dev/null|head -n1|${SED} -re "s/^(${gyaml_param}): (.*)$/\2/g"
}

edit_yaml_file() {
    yaml_old_value=""
    yaml_file_changed="0"
    yaml_param="${1}"
    yaml_value="${2}"
    shift
    shift
    yaml_file=${1}
    yaml_edit_value="0"
    yaml_edited_value="0"
    yaml_added_value="0"
    yaml_add_value="0"
    if [ -e "${yaml_file}" ] && [ ! -d "${yaml_file}" ];then
        if [ "x$(egrep -h -q "^${yaml_param}: " ${@} 2>/dev/null;echo ${?})" = "x0" ];then
            yaml_edit_value="1"
        fi
        if [ "x${yaml_edit_value}" != "x0" ];then
            yaml_old_value=$(get_yaml_value "${yaml_param}" ${@})
            if [ "x${yaml_old_value}" != "x${yaml_value}" ];then
                yaml_file_changed="1"
                yaml_edited_value="1"
                yaml_add_value="1"
                ${SED} -i -re "/^${yaml_param}: /d" ${@}
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
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    branch_id="$(sanitize_changeset $(get_ms_branch))"
    master="${1:-${MASTERSALT_MASTER_DNS}}"
    master_ip="${2:-${MASTERSALT_MASTER_IP}}"
    port="${3:-${MASTERSALT_MASTER_PORT}}"
    publish_port="${4:-${MASTERSALT_MASTER_PUBLISH_PORT}}"
    mastersalt_master_changed="${mastersalt_master_changed:-"0"}"
    if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
        for conf in "${MASTERSALT_PILLAR}/mastersalt_minion.sls" "${MASTERSALT_PILLAR}/mastersalt.sls";do
            if [ ! -e "${conf}" ];then
                touch "${conf}"
            fi
            edit_yaml_file makina-states.controllers.mastersalt_master.settings.interface "${master_ip}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_master_changed="1"
            fi
            edit_yaml_file makina-states.controllers.mastersalt_master.settings.publish_port "${publish_port}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_master_changed="1"
            fi
            edit_yaml_file makina-states.controllers.mastersalt_master.settings.ret_port "${port}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_master_changed="1"
            fi
        done
        confs=""
        for conf in "${MCONF_PREFIX}"/master "${MCONF_PREFIX}"/master.d/*;do
            if [ -f "${conf}" ];then
                congs="${confs} ${conf}"
            fi
        done
        edit_yaml_file interface "${SALT_MASTER_IP}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_master_changed="1"
        fi
        edit_yaml_file ret_port "${SALT_MASTER_PORT}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_master_changed="1"
        fi
        edit_yaml_file publish_port "${SALT_MASTER_PUBLISH_PORT}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_master_changed="1"
        fi
        edit_yaml_file "${BRANCH_PILLAR_ID}" "${branch_id}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_master_changed="1"
        fi
        edit_yaml_file makina-states.controllers.mastersalt_master true "${MCONF_PREFIX}/grains"
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_master_changed="1"
        fi
    else
        if [ "x${IS_MASTERSALT}" != "x" ];then
            edit_yaml_file makina-states.controllers.mastersalt_master false "${MCONF_PREFIX}/grains"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_master_changed="1"
            fi
        fi
    fi
}

reconfigure_salt_master() {
    if [ "x${DO_SALT}" = "xno" ];then return;fi
    branch_id="$(sanitize_changeset $(get_ms_branch))"
    master="${1:-${SALT_MASTER_DNS}}"
    master_ip="${2:-${SALT_MASTER_IP}}"
    port="${3:-${SALT_MASTER_PORT}}"
    publish_port="${4:-${SALT_MASTER_PUBLISH_PORT}}"
    salt_master_changed="${salt_master_changed:-"0"}"
    if [ "x${IS_SALT_MASTER}" != "x" ];then
        for conf in "${SALT_PILLAR}/salt_minion.sls" "${SALT_PILLAR}/salt.sls";do
            if [ ! -e "${conf}" ];then
                touch "${conf}"
            fi
            # think to firewall the interfaces, but restricting only to localhost cause
            # more harm than good
            # any way the keys for attackers need to be accepted.
            edit_yaml_file makina-states.controllers.salt_master.settings.interface "${master_ip}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_master_changed="1"
            fi
            edit_yaml_file makina-states.controllers.salt_master.settings.publish_port "${publish_port}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_master_changed="1"
            fi
            edit_yaml_file makina-states.controllers.salt_master.settings.ret_port "${port}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_master_changed="1"
            fi
            edit_yaml_file "${BRANCH_PILLAR_ID}" "${branch_id}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_master_changed="1"
            fi
        done
        confs=""
        for conf in "${CONF_PREFIX}"/master "${CONF_PREFIX}"/master.d/*;do
            if [ -f "${conf}" ];then
                confs="${confs} ${conf}"
            fi
        done
        edit_yaml_file interface "${master_ip}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            salt_master_changed="1"
        fi
        edit_yaml_file ret_port "${port}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            salt_master_changed="1"
        fi
        edit_yaml_file publish_port "${publish_port}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            salt_master_changed="1"
        fi
        edit_yaml_file makina-states.controllers.salt_master true "${CONF_PREFIX}/grains"
        if [ "x${yaml_file_changed}" != "x0" ];then
            salt_master_changed="1"
        fi
    else
        if [ "x${IS_SALT}" != "x" ];then
            edit_yaml_file makina-states.controllers.salt_master false "${CONF_PREFIX}/grains"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_master_changed="1"
            fi
        fi
    fi
}

reconfigure_mastersalt_minion() {
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    branch_id="$(sanitize_changeset $(get_ms_branch))"
    setted_id="${1:-$(get_minion_id)}"
    master="${1:-${MASTERSALT_MASTER_DNS}}"
    port="${2:-${MASTERSALT_MASTER_PORT}}"
    minion_ip="${3:-${MASTERSALT_MINION_IP}}"
    mastersalt_minion_changed="${mastersalt_minion_changed:-"0"}"
    if [ "x${IS_MASTERSALT_MINION}" != "x" ];then
        for i in "${MCONF_PREFIX}/minion_id";do
            if [ -f "${i}" ];then
                echo "${setted_id}" > "${i}"
            fi
        done
        "${SED}" -i -re "/^id:/d" "${MASTERSALT_PILLAR}/mastersalt_minion.sls"
        "${SED}" -i -re "/^makina-states.minion_id:/d" "${MASTERSALT_PILLAR}/mastersalt_minion.sls"
        for conf in "${MCONF_PREFIX}/grains" "${MASTERSALT_PILLAR}/mastersalt.sls";do
            if [ ! -e "${conf}" ];then
                touch "${conf}"
            fi
            "${SED}" -i -e "/^    id:/ d" "${conf}"
            edit_yaml_file id "${setted_id}" ${conf}
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_minion_changed="1"
            fi
            edit_yaml_file makina-states.minion_id "${setted_id}" ${conf}
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_minion_changed="1"
            fi
        done
        for conf in "${MASTERSALT_PILLAR}/mastersalt_minion.sls" "${MASTERSALT_PILLAR}/mastersalt.sls";do
            edit_yaml_file makina-states.controllers.mastersalt_minion.settings.master "${master}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_minion_changed="1"
            fi
            edit_yaml_file makina-states.controllers.mastersalt_minion.settings.master_port "${port}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_minion_changed="1"
            fi
            edit_yaml_file "${BRANCH_PILLAR_ID}" "${branch_id}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_minion_changed="1"
            fi
            edit_yaml_file makina-states.controllers.mastersalt_minion.settings.interface "${minion_ip}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
        done
        confs=""
        for conf in "${MCONF_PREFIX}"/minion "${MCONF_PREFIX}"/minion.d/*;do
            if [ -f "${conf}" ];then
                confs="${confs} ${conf}"
            fi
        done
        "${SED}" -i -e "/^    id:/ d" "${conf}"
        edit_yaml_file id "${setted_id}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_minion_changed="1"
        fi
        edit_yaml_file interface "${minion_ip}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_minion_changed="1"
        fi
        edit_yaml_file master "${master}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_minion_changed="1"
        fi
        edit_yaml_file master_port "${port}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_minion_changed="1"
        fi
        edit_yaml_file makina-states.minion_id "${setted_id}" "${MCONF_PREFIX}/grains"
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_minion_changed="1"
        fi
        edit_yaml_file makina-states.controllers.mastersalt_minion true "${MCONF_PREFIX}/grains"
        if [ "x${yaml_file_changed}" != "x0" ];then
            mastersalt_minion_changed="1"
        fi
    else
        if [ "${IS_SALT}" != "x" ];then
            edit_yaml_file makina-states.controllers.mastersalt_minion false "${MCONF_PREFIX}/grains"
            if [ "x${yaml_file_changed}" != "x0" ];then
                mastersalt_minion_changed="1"
            fi
        fi
    fi
}

reconfigure_salt_minion() {
    if [ "x${DO_SALT}" = "xno" ];then return;fi
    branch_id="$(sanitize_changeset $(get_ms_branch))"
    setted_id="${1:-$(get_minion_id)}"
    master="${1:-${SALT_MASTER_DNS}}"
    port="${2:-${SALT_MASTER_PORT}}"
    minion_ip="${2:-${SALT_MINION_IP}}"
    salt_minion_changed="${salt_minion_changed:-"0"}"
    if [ "x${IS_SALT_MINION}" != "x" ];then
        for i in "${CONF_PREFIX}/minion_id";do
            if [ -f "${i}" ];then
                echo "${setted_id}" > "${i}"
            fi
        done
        "${SED}" -i -re "/^id:/d" "${SALT_PILLAR}/salt_minion.sls"
        "${SED}" -i -re "/^makina-states.minion_id:/d" "${SALT_PILLAR}/salt_minion.sls"
        for conf in "${CONF_PREFIX}/grains" "${SALT_PILLAR}/salt.sls";do
            if [ ! -e "${conf}" ];then
                touch "${conf}"
            fi
            "${SED}" -i -e "/^    id:/ d" "${conf}"
            edit_yaml_file id "${setted_id}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
            edit_yaml_file makina-states.minion_id "${setted_id}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
        done
        for conf in "${SALT_PILLAR}/salt_minion.sls" "${SALT_PILLAR}/salt.sls";do
            edit_yaml_file makina-states.controllers.salt_minion.settings.master "${master}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
            edit_yaml_file makina-states.controllers.salt_minion.settings.master_port "${port}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
            edit_yaml_file "${BRANCH_PILLAR_ID}" "${branch_id}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
            edit_yaml_file makina-states.controllers.salt_minion.settings.interface "${minion_ip}" "${conf}"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
        done
        conf=""
        for conf in "${CONF_PREFIX}"/minion "${CONF_PREFIX}"/minion.d/*;do
            if [ -f "${conf}" ];then
                confs="${confs} ${conf}"
             fi
        done
        edit_yaml_file id "${setted_id}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            salt_minion_changed="1"
        fi
        edit_yaml_file master "${master}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            salt_minion_changed="1"
        fi
        edit_yaml_file master_port "${port}" ${confs}
        if [ "x${yaml_file_changed}" != "x0" ];then
            salt_minion_changed="1"
        fi
        edit_yaml_file makina-states.controllers.salt_minion true "${CONF_PREFIX}/grains"
        if [ "x${yaml_file_changed}" != "x0" ];then
            salt_minion_changed="1"
        fi
    else
        if [ "${IS_MASTERSALT}" != "x" ];then
            edit_yaml_file makina-states.controllers.salt_minion false "${CONF_PREFIX}/grains"
            if [ "x${yaml_file_changed}" != "x0" ];then
                salt_minion_changed="1"
            fi
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
    touch "${SALT_PILLAR}/salt.sls" "${SALT_PILLAR}/salt_minion.sls"
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
        touch "${MASTERSALT_PILLAR}/mastersalt.sls" "${MASTERSALT_PILLAR}/mastersalt_minion.sls"
    fi
}

maybe_wire_reattached_conf() {
    # install salt cloud keys &  reconfigure any preprovisionned daemons
    if [ "x${SALT_REATTACH}" != "x" ];then
        bs_log "SaltCloud mode: killing daemons"
        kill_ms_daemons
        # remove any provisionned init overrides
        if find /etc/init/*salt*.override -type f 1>/dev/null 2>/dev/null;then
            bs_log "SaltCloud mode: removing upstart init stoppers"
            rm -fv /etc/init/*salt*.override
        fi
        bs_log "SaltCloud mode: Resetting some configurations"
        if [ "x${IS_MASTERSALT}" != "x" ];then
            gen_mastersalt_keys
        fi
        if [ "x${IS_SALT}" != "x" ];then
            # force regenerate keys for the local master
            rm -f "${CONF_PREFIX}/pki/minion/minion_master.pub"
            bs_log "SaltCloud mode: Installing keys"
            gen_salt_keys
        fi
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
                | ${SED} -re "s/],$/]/g" \
                | ${SED} -re "s/^  +\"([^:]+: )/\"\1/g" \
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
            | ${SED} -re "s/],$/]/g" \
            | ${SED} -re "s/^  +\"([^:]+: )/\"\1/g" \
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
            | ${SED} -re "s/^  +\"([^:]+: )/\"\1/g" \
            | ${SED} -re "s/],$/]/g" \
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
            | ${SED} -re "s/^  +\"([^:]+: )/\"\1/g" \
            | ${SED} -re "s/],$/]/g" \
            >> "${conf_prefix}/minion"
        fi
    fi
}

create_salt_skeleton() {
    check_ssh_keys
    create_core_conf
    create_pillars
    create_salt_tops
    create_pillar_tops
    maybe_wire_reattached_conf
    reconfigure_masters
    reconfigure_minions
}

# ------------ SALT INSTALLATION PROCESS

mastersalt_master_processes() {
    filter_host_pids $(${PS} aux|grep salt-master|grep -v "bin/sh -ec"|grep -v deploy.sh|grep -v boot-salt|grep -v bootstrap.sh|grep mastersalt|grep -v grep|awk '{print $2}')|wc -w|${SED} -e "s/ //g"
}

mastersalt_minion_processes() {
    filter_host_pids $(${PS} aux|grep salt-minion|grep -v "bin/sh -ec"|grep -v deploy.sh|grep -v boot-salt|grep -v bootstrap.sh|grep mastersalt|grep -v grep|awk '{print $2}')|wc -w|${SED} -e "s/ //g"
}

master_processes() {
    filter_host_pids $(${PS} aux|grep salt-master|grep -v "bin/sh -ec"|grep -v deploy.sh|grep -v boot-salt|grep -v bootstrap.sh|grep -v mastersalt|grep -v grep|awk '{print $2}')|wc -w|${SED} -e "s/ //g"
}


minion_processes() {
    filter_host_pids $(${PS} aux|grep salt-minion|grep -v "bin/sh -ec"|grep -v deploy.sh|grep -v boot-salt|grep -v bootstrap.sh|grep -v mastersalt|grep -v grep|awk '{print $2}')|wc -w|${SED} -e "s/ //g"
}

lazy_start_salt_daemons() {
    if [ "x${DO_SALT}" = "xno" ];then return;fi
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

is_same() {
    ret=1
    if [ -e "${1}" ] && [ -e "${2}" ];then
        diff -aq "${1}" "${2}" 1>/dev/null 2>/dev/null
        ret=${?}
    fi
    return ${ret}
}


test_reattached_keys() {
    if [ "x${SALT_REATTACH}" != "x" ]\
        && [ -e "${SALT_REATTACH_DIR}/minion.pem" ] \
        && [ -e "${SALT_REATTACH_DIR}/minion.pub" ];then
        alreadydone="y"
        if ! is_same "${SALT_REATTACH_DIR}/minion.pub" "${MCONF_PREFIX}/pki/minion/minion.pub";then
            alreadydone=""
        fi
        if ! is_same "${SALT_REATTACH_DIR}/minion.pem" "${MCONF_PREFIX}/pki/minion/minion.pem";then
            alreadydone=""
        fi
        if [ "x${alreadydone}" != "x" ];then
            return 1
        else
            return 0
        fi
    fi
    return 1
}

gen_mastersalt_keys() {
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    if [ "x${IS_MASTERSALT_MASTER}" != "x" ]\
        && [ ! -e "${MCONF_PREFIX}/pki/master/master.pub" ];then
        bs_log "Generating mastersalt master key"
        "${MASTERSALT_MS}/bin/salt-key" -c "${MCONF_PREFIX}" --gen-keys=master --gen-keys-dir="${MCONF_PREFIX}/pki/master"
        BS_MS_ASSOCIATION_RESTART_MASTER="1"
    fi
    if [ "x${IS_MASTERSALT_MINION}" != "x" ]\
        && ! test_reattached_keys\
        && [ ! -e "${MCONF_PREFIX}/pki/minion/minion.pub" ];then
        bs_log "Generating mastersalt minion key"
        "${MASTERSALT_MS}/bin/salt-key" -c "${MCONF_PREFIX}" --gen-keys=minion --gen-keys-dir="${MCONF_PREFIX}/pki/minion"
        BS_MS_ASSOCIATION_RESTART_MINION="1"
    fi
    if test_reattached_keys;then
        bs_log "SaltCloud mode: Resetting some mastersalt configurations"
        __install "${SALT_REATTACH_DIR}/minion.pub" "${MCONF_PREFIX}/pki/minion/minion.pub"
        __install "${SALT_REATTACH_DIR}/minion.pem" "${MCONF_PREFIX}/pki/minion/minion.pem"
        __install "${SALT_REATTACH_DIR}/minion.pub" "${CONF_PREFIX}/pki/minion/minion.pub"
        __install "${SALT_REATTACH_DIR}/minion.pem" "${CONF_PREFIX}/pki/minion/minion.pem"
        if [ -e "${MCONF_PREFIX}/pki/master/minions" ];then
            __install "${SALT_REATTACH_DIR}/minion.pub" "${MCONF_PREFIX}/pki/master/minions/$(get_minion_id)"
        fi
        if [ -e "${CONF_PREFIX}/pki/master/minions" ];then
            __install "${SALT_REATTACH_DIR}/minion.pub" "${CONF_PREFIX}/pki/master/minions/$(get_minion_id)"
        fi
        if [ -e "${CONF_PREFIX}/pki/master/master.pub" ] && [ -e "${CONF_PREFIX}/pki/minion" ];then
            __install "${CONF_PREFIX}/pki/master/master.pub" "${CONF_PREFIX}/pki/minion/minion_master.pub"
        fi

        BS_MS_ASSOCIATION_RESTART_MINION="1"
        BS_MS_ASSOCIATION_RESTART_MASTER="1"
        BS_ASSOCIATION_RESTART_MASTER="1"
        BS_ASSOCIATION_RESTART_MINION="1"
    fi
    if [ "x${IS_MASTERSALT_MINION}" != "x" ] && [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
        if ! is_same "${MCONF_PREFIX}/pki/minion/minion.pub" "${MCONF_PREFIX}/pki/master/minions/$(get_minion_id)";then
            __install "${MCONF_PREFIX}/pki/minion/minion.pub" "${MCONF_PREFIX}/pki/master/minions/$(get_minion_id)"
            BS_MS_ASSOCIATION_RESTART_MASTER="1"
            BS_MS_ASSOCIATION_RESTART_MINION="1"
        fi
        if ! is_same "${MCONF_PREFIX}/pki/master/master.pub" "${MCONF_PREFIX}/pki/minion/minion_master.pub";then
            __install "${MCONF_PREFIX}/pki/master/master.pub" "${MCONF_PREFIX}/pki/minion/minion_master.pub"
            BS_MS_ASSOCIATION_RESTART_MINION="1"
        fi
    fi
}

gen_salt_keys() {
    if [ "x${DO_SALT}" = "xno" ];then return;fi
    if [ "x${IS_SALT_MASTER}" != "x" ] && [ ! -e "${CONF_PREFIX}/pki/master/master.pub" ];then
        bs_log "Generating salt minion key"
        "${SALT_MS}/bin/salt-key" -c "${CONF_PREFIX}" --gen-keys=master --gen-keys-dir=${CONF_PREFIX}/pki/master
        BS_ASSOCIATION_RESTART_MASTER="1"
    fi
    # in saltcloude mode, keys are already providen
    if [ "x${IS_SALT_MINION}" != "x" ] && [ ! -e "${CONF_PREFIX}/pki/minion/minion.pub" ];then
        bs_log "Generating salt minion key"
        "${SALT_MS}/bin/salt-key" -c "${CONF_PREFIX}" --gen-keys=minion --gen-keys-dir=${CONF_PREFIX}/pki/minion
        BS_ASSOCIATION_RESTART_MINION="1"
    fi
    if [ "x${IS_SALT_MINION}" != "x" ] && [ "x${IS_SALT_MASTER}" != "x" ];then
        if ! is_same "${CONF_PREFIX}/pki/minion/minion.pub" "${CONF_PREFIX}/pki/master/minions/$(get_minion_id)";then
            __install "${CONF_PREFIX}/pki/minion/minion.pub" "${CONF_PREFIX}/pki/master/minions/$(get_minion_id)"
            BS_ASSOCIATION_RESTART_MASTER="1"
            BS_ASSOCIATION_RESTART_MINION="1"
        fi
        if ! is_same "${CONF_PREFIX}/pki/master/master.pub" "${CONF_PREFIX}/pki/minion/minion_master.pub";then
            __install "${CONF_PREFIX}/pki/master/master.pub" "${CONF_PREFIX}/pki/minion/minion_master.pub"
            BS_ASSOCIATION_RESTART_MINION="1"
        fi
    fi
}


install_salt_daemons() {
    if [ "x${DO_SALT}" = "xno" ];then return;fi
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
            && [ ! -f "${ETC_SYSTEMD}/salt-master.service" ]\
            && [ ! -e "${ETC_INIT}.d/salt-master" ];then
            RUN_SALT_BOOTSTRAP="1"
        fi
    fi
    if [ "x${IS_SALT_MINION}" != "x" ];then
        if [ ! -e "${ETC_INIT}/salt-minion.conf" ]\
            && [ ! -f "${ETC_SYSTEMD}/salt-minion.service" ]\
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
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    if [ ! -e "${ALIVE_MARKER}" ];then
        kill_pids $(filter_host_pids $(${PS} aux|egrep "salt-(master|syndic)"|grep -v deploy.sh|grep -v bootstrap.sh|grep -v boot-salt|grep mastersalt|awk '{print $2}')) 1>/dev/null 2>/dev/null
    fi
}

killall_local_mastersalt_minions() {
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    if [ ! -e "${ALIVE_MARKER}" ];then
        kill_pids $(filter_host_pids $(${PS} aux|egrep "salt-(minion)"|grep -v deploy.sh|grep -v bootstrap.sh|grep -v boot-salt|grep mastersalt|awk '{print $2}')) 1>/dev/null 2>/dev/null
    fi
}

killall_local_masters() {
    if [ "x${DO_SALT}" = "xno" ];then return;fi
    if [ ! -e "${ALIVE_MARKER}" ];then
        kill_pids $(filter_host_pids $(${PS} aux|egrep "salt-(master|syndic)"|grep -v deploy.sh|grep -v bootstrap.sh|grep -v boot-salt|grep -v mastersalt|awk '{print $2}')) 1>/dev/null 2>/dev/null
    fi
}

killall_local_minions() {
    if [ "x${DO_SALT}" = "xo" ];then return;fi
    if [ ! -e "${ALIVE_MARKER}" ];then
        kill_pids $(filter_host_pids $(${PS} aux|egrep "salt-(minion)"|grep -v deploy.sh|grep -v bootstrap.sh|grep -v boot-salt|grep -v mastersalt|awk '{print $2}')) 1>/dev/null 2>/dev/null
    fi
}

restart_local_mastersalt_masters() {
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    if [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then
        stop_and_disable_service mastersalt-master
    else
        enable_service mastersalt-master
        if [ ! -e "${ALIVE_MARKER}" ] && [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
            service memcached restart 1>/dev/null 2>/dev/null
            service_ mastersalt-master stop
            killall_local_mastersalt_masters
            service_ mastersalt-master restart
        fi
    fi
    mastersalt_master_changed="0"
}

restart_local_mastersalt_minions() {
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    if [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then
        killall_local_mastersalt_minions
        stop_and_disable_service mastersalt-minion
    else
        enable_service mastersalt-minion
        if [ ! -e "${ALIVE_MARKER}" ] && [ "x${IS_MASTERSALT_MINION}" != "x" ];then
            service_ mastersalt-minion stop
            killall_local_mastersalt_minions
            service_ mastersalt-minion restart
        fi
    fi
    mastersalt_minion_changed="0"
}

restart_local_masters() {
    if [ "x${DO_SALT}" = "xno" ];then return;fi
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
    if [ "x${DO_SALT}" = "xno" ];then return;fi
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
    if [ "x${DO_SALT}" = "xno" ];then return;fi
    # test in a subshell as this can be bloquant
    # salt cloud would then fail badly on this
    if [ x"${local_salt_mode}" = "xmasterless" ];then return;fi
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
        return 256
    fi
    rm -f "${SALT_BOOT_LOCK_FILE}" "${LAST_RETCODE_FILE}"
    return ${last_salt_retcode}
}

mastersalt_ping_test() {
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    if [ x"${local_mastersalt_mode}" = "xmasterless" ];then return;fi
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
        return 256
    fi
    rm -f "${SALT_BOOT_LOCK_FILE}" "${LAST_RETCODE_FILE}"
    return ${last_salt_retcode}
}

minion_challenge() {
    if [ "x${DO_SALT}" = "xno" ];then return;fi
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
        restart_local_minions
        resultping="1"
        for j in `seq ${inner_tries}`;do
            if ! salt_ping_test;then
                bs_yellow_log " sub challenge try (${i}/${global_tries}) (${j}/${inner_tries})"
                sleep 1
            else
                resultping="0"
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
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
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
        restart_local_mastersalt_minions
        resultping="1"
        for j in `seq ${inner_tries}`;do
            if ! mastersalt_ping_test;then
                bs_yellow_log " sub challenge try (${i}/${global_tries}) (${j}/${inner_tries})"
                sleep 1
            else
                resultping="0"
                break
            fi
        done
        if [ "x${resultping}" != "x0" ];then
            bs_log "Failed challenge mastersalt keys on $(get_mastersalt), retry ${i}/${global_tries}"
            challenged_ms=""
        else
            challenged_ms="y"
            bs_log "Successfull challenge mastersalt keys on $(get_mastersalt)"
            break
        fi
    done
}

salt_master_connectivity_check() {
    if [ "x${DO_SALT}" = "xno" ];then return;fi
    if [ "x$(get_local_salt_mode)" != "xmasterless" ];then
        if [ "x$(check_connectivity ${SALT_MASTER_IP} ${SALT_MASTER_PORT} 30)" != "x0" ];then
            die "SaltMaster is unreachable (${SALT_MASTER_IP}/${SALT_MASTER_PORT})"
        fi
    fi
}

mastersalt_master_connectivity_check() {
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    if [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then return;fi
    if [ "x$(check_connectivity $(get_mastersalt) ${MASTERSALT_MASTER_PORT} 30)" != "x0" ];then
        die "MastersaltMaster is unreachable ($(get_mastersalt)/${MASTERSALT_MASTER_PORT})"
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
    if [ "x$(get_salt_nodetype)" = "xtravis" ];then
        echo 15
    else
        echo 3
    fi
}

make_association() {
    if [ "x${DO_SALT}" = "xno" ];then return;fi
    if [ "x${IS_SALT_MINION}" = "x" ];then return;fi
    if [ "x$(get_local_salt_mode)" = "xmasterless" ];then
        registered="1"
        minion_id="$(get_minion_id)"
        return;
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
    if [ "x${BS_ASSOCIATION_RESTART_MASTER}" != "x" ];then
        restart_local_masters
        if [ "x$(get_local_salt_mode)" != "xmasterless" ];then
            sleep 10
        fi
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
        bs_log "Salt minion \"${minion_id}\" already registered on master"
        minion_id="$(get_minion_id)"
        registered="1"
    else
        if [ "x${SALT_MASTER_DNS}" = "xlocalhost" ];then
            debug_msg "Forcing salt master restart"
            restart_local_masters
            if [ "x$(get_local_salt_mode)" != "xmasterless" ];then
                sleep 10
            fi
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
        if salt_ping_test && [ "x${minion_keys}" != "x0" ];then
            # sleep 15 seconds giving time for the minion to wake up
            bs_log "Salt minion \"${minion_id}\" registered on master"
            registered="1"
        else
            minion_challenge
            if [ "x${challenged_ms}" = "x" ];then
                bs_log "Failed accepting salt key on master for ${minion_id}"
                exit 1
            fi
            minion_id="$(get_minion_id)"
            registered="1"
            bs_log "salt minion already registered"
        fi
        if [ "x${registered}" = "x" ];then
            bs_log "Failed accepting salt key on ${SALT_MASTER_IP} for ${minion_id}"
            exit 1
        fi
    fi
}

challenge_mastersalt_message() {
    minion_id="$(get_minion_id)"
    if [ "x${QUIET}" = "x" ]; then
        bs_log "****************************************************************"
        bs_log "    GO ACCEPT THE KEY ON MASTERSALT ($(get_mastersalt)) !!! "
        bs_log "    You need on this box to run mastersalt-key -y -a ${minion_id}"
        bs_log "****************************************************************"
    fi
}

make_mastersalt_association() {
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    if [ "x${IS_MASTERSALT_MINION}" = "x" ];then return;fi
    if [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then return;fi
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
    if mastersalt_ping_test;then
        bs_log "Mastersalt minion \"${minion_id}\" already registered on $(get_mastersalt)"
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
                    exit 1
                else
                    bs_log "Accepted mastersalt key"
                fi
            fi
        fi
        if [ "x${BS_MS_ASSOCIATION_RESTART_MASTER}" != "x" ];then
            bs_log "Forcing mastersalt master restart"
            restart_local_mastersalt_masters
            sleep 10
        fi
        debug_msg "Forcing mastersalt minion restart"
        if [ "x${BS_MS_ASSOCIATION_RESTART_MINION}" != "x" ];then
            bs_log "Forcing mastersalt minion restart"
            restart_local_mastersalt_minions
        fi
        mastersalt_master_connectivity_check
        bs_log "Waiting for mastersalt minion key hand-shake"
        minion_id="$(get_minion_id)"
        if mastersalt_ping_test;then
            bs_log "Mastersalt minion \"${minion_id}\" registered on master"
            registered="1"
        else
            mastersalt_minion_challenge
            if [ "x${challenged_ms}" = "x" ];then
                bs_log "Failed accepting salt key on master for ${minion_id}"
                exit 1
            fi
            minion_id="$(get_minion_id)"
            registered="1"
            bs_log "salt minion registered"
        fi
        if [ "x${registered}" = "x" ];then
            bs_log "Failed accepting mastersalt key on $(get_mastersalt) for ${minion_id}"
            exit 1
        fi
    fi
}

lazy_start_mastersalt_daemons() {
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    if [ "x$(get_local_mastersalt_mode)" = "xmasterless" ];then return;fi
    if [ "x${IS_MASTERSALT_MASTER}" != "x" ];then
        if [ "x$(mastersalt_master_processes)" = "x0" ] || [ "x${mastersalt_master_changed}" = "x1" ];then
            restart_local_mastersalt_masters
            sleep 2
            if [ "x$(mastersalt_master_processes)" = "x0" ];then
                die "Masteralt Master start failed"
            fi
        fi
    fi
    if [ "x${IS_MASTERSALT_MINION}" != "x" ] || [ "${mastersalt_minion_changed}" = "x1" ];then
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

install_nodetype() {
    if [ "x${DO_NODETYPE_INSTALL}" != "x" ];then
        # run mastersalt master+minion boot_nodetype bootstrap
        ${SED} -i -e "/makina-states.nodetypes.$(get_salt_nodetype):/ d"  "${MCONF_PREFIX}/grains"
        echo "makina-states.nodetypes.$(get_salt_nodetype): true" >> "${MCONF_PREFIX}/grains"
        if [ "x$(get_salt_nodetype)" != "xscratch" ]; then
            run_mastersalt_bootstrap ${mastersalt_bootstrap_nodetype}
        fi
    else:
        bs_log "Nodetype bootstrap for $(get_salt_nodetype) skipped"
    fi
}

install_mastersalt_daemons() {
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    # --------- check if we need to run mastersalt setup's
    RUN_MASTERSALT_BOOTSTRAP="${SALT_REBOOTSTRAP}"
    # regenerate keys if missing or reattach keys from new mastersalt
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
            &&  [ ! -f "${ETC_SYSTEMD}/mastersalt-master.service" ]\
            &&  [ ! -e "${ETC_INIT}/mastersalt-master.conf" ];then
            RUN_MASTERSALT_BOOTSTRAP="1"
        fi
    fi
    if  [ "x${IS_MASTERSALT_MINION}" != "x" ];then
        if [ ! -e "${ETC_INIT}.d/mastersalt-minion" ]\
            &  [ ! -f "${ETC_SYSTEMD}/mastersalt-minion.service" ]\
            && [ ! -e "${ETC_INIT}/mastersalt-minion.conf" ];then
            RUN_MASTERSALT_BOOTSTRAP="1"
        fi
    fi
    if [  "${SALT_BOOT_DEBUG}" != "x" ];then
        debug_msg "mastersalt:"
        debug_msg "RUN_MASTERSALT_BOOTSTRAP: ${RUN_MASTERSALT_BOOTSTRAP}"
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

        # run mastersalt master setup
        if [ "x${IS_MASTERSALT_MASTER}" != "x" ] && [ "x$(get_local_mastersalt_mode)" != "xmasterless" ];then
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
            if [ "x$(get_local_mastersalt_mode)" != "xmasterless" ];then
                sleep 10
            fi
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
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
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
}

# --------- HIGH-STATES

highstate_in_mastersalt_env() {
    if [ "x$(get_do_mastersalt)" = "xno" ];then return;fi
    # IMPORTANT: MASTERSALT BEFORE SALT !!!
    if [ "x${SALT_BOOT_SKIP_HIGHSTATES}" = "x" ]\
        && [ "x${MASTERSALT_BOOT_SKIP_HIGHSTATE}" = "x" ];then
        bs_log "Running makina-states highstate for mastersalt"
        bs_log "    export MASTERSALT_BOOT_SKIP_HIGHSTATE=1 to skip (dangerous)"
        LOCAL=""
        if ! mastersalt_ping_test;then
            LOCAL="--local ${LOCAL}"
            bs_yellow_log " [bs] mastersalt highstate running offline !"
        fi
        mastersalt_call_wrapper ${LOCAL} state.highstate
        if [ "x${last_salt_retcode}" != "x0" ];then
            bs_log "Failed highstate for mastersalt"
            exit 1
        fi
    else
        bs_log "mastersalt highstate skipped"
    fi
}

highstate_in_salt_env() {
    if [ "x${DO_SALT}" = "xno" ];then return;fi
    if [ "x${SALT_BOOT_SKIP_HIGHSTATES}" = "x" ]\
        && [ "x${SALT_BOOT_SKIP_HIGHSTATE}" = "x" ];then
        bs_log "Running makina-states highstate"
        bs_log "    export SALT_BOOT_SKIP_HIGHSTATE=1 to skip (dangerous)"
        LOCAL=""
        if ! salt_ping_test;then
            bs_yellow_log " [bs] salt highstate running offline !"
            LOCAL="--local ${LOCAL}"
        fi
        salt_call_wrapper ${LOCAL} state.highstate
        if [ "x${last_salt_retcode}" != "x0" ];then
            bs_log "Failed highstate"
            exit 1
        fi
    else
        bs_log "salt highstate skipped"
    fi
}

run_highstates() {
    highstate_in_salt_env
    highstate_in_mastersalt_env
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
        exemple ":" "install a saltmaster/minion on the first run and run highstates after"
        exemple " --nodetype=devhost" "install a saltmaster/minion in 'development' mode"
        exemple " --mastersalt mastersalt.mycompany.net" "install a mastersalt minion linked to mastersalt.mycompany.net"
    fi
    echo
    bs_log "  General settings"
    bs_help "    -b|--branch <branch>" "MakinaStates branch to use" "$(get_ms_branch)" y
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
    bs_help "    --synchronize-deps" "When sync sourcecode, also get git dependencies" "${SALT_BOOT_SYNC_DEPS}" y
    bs_help "    --cleanup" "Cleanup old execution logfiles" "${SALT_BOOT_CLEANUP}" y
    bs_help "    --reattach" "Reattach a mastersalt minion ba${SED} install to a new master (saltcloud/config.seed) (need new key/confs via --reattach-dir)" "${SALT_REATTACH}" y
    if [ "x${SALT_LONG_HELP}" != "x" ];then
        bs_help "    --salt-rebootstrap" "Redo salt bootstrap" "${SALT_REBOOTSTRAP}" "y"
        bs_help "    --venv-rebootstrap" "Redo venv, salt bootstrap" "${VENV_REBOOTSTRAP}" "y"
    fi
    bs_log "  Actions settings"
    bs_help "    -g|--makina-states-url <url>" "makina-states git url" "$(get_ms_url)" y
    bs_help "    --salt-url <url>" "saltstack fork git url" "$(get_salt_url)" y
    bs_help "    --salt-branch <branch>" "saltstack fork git branch" "$(get_salt_branch)" y
    bs_help "    --reattach-dir" "for --reattach, the directory to grab salt master/minion new keys & conf from" "${SALT_REATTACH_DIR}" y
    if [ "x${SALT_LONG_HELP}" != "x" ];then
        bs_help "    -r|--root <path>" "/ path" "${ROOT}"
        bs_help "    -p|--prefix <path>" "prefix path" "${PREFIX}" yi
    fi
    bs_log "  Switches"
    bs_help "    --only-nodetype" "Do only nodetype bootstrap states" "" y
    bs_help "    --only-salt" "Do only salt states" "" y
    bs_help "    --only-mastersalt" "Do only mastersalt states" "" y
    bs_help "    --no-nodetype" "Do not run nodetype bootstrap" "" y
    bs_help "    --no-mastersalt" "Do not install mastersalt daemons" "" y
    bs_help "    --no-salt" "Do not install salt daemons" "" y
    bs_help "    --pack" "Do run git pack (gc) if necessary" "" y
    bs_help "    --only-pack" "Do run git pack (gc) if necessary and skip any further step" "" y
    bs_help "    --only-prereqs" "Do only pre install steps" "" y
    bs_help "    --only-install-saltenvs" "Do not go further than installing salt envs" "" y
    bs_help "    --no-ms-venv-cache" "Do not try to download prebuilt virtualenvs" "" y
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
    bs_help "    --mastersalt <FQDN>" "DNS address of the mastersalt master" "${MASTERSALT_MASTER_DNS}" y
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
            FORCE_LOCAL_MASTERSALT_MODE="remote"
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
        if [ "x${1}" = "x--force-pip-install" ];then
            DO_MS_PIP="y";DO_PIP="y";argmatch="1"
        fi
        if [ "x${1}" = "x-C" ] || [ "x${1}" = "x--no-confirm" ];then
            SALT_BOOT_NOCONFIRM="y";argmatch="1"
        fi
        if [ "x${1}" = "x--no-ms-venv-cache" ];then
            NO_MS_VENV_CACHE="y";argmatch="1"
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
        # do not remove yet for retro compat
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
        if [ "x${1}" = "x--only-pack" ];then
            FORCE_GIT_PACK="1"
            ONLY_GIT_PACK="1"
            argmatch="1"
        fi
        if [ "x${1}" = "x--pack" ];then
            FORCE_GIT_PACK="1"
            argmatch="1"
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
        if [ "x${1}" = "x--synchronize-deps" ];then
            SALT_BOOT_SYNC_DEPS="1"
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
        if [ "x${1}" = "x--only-prereqs" ];then
            SALT_BOOT_ONLY_PREREQS="yes"
            argmatch="1"
        fi
        if [ "x${1}" = "x--only-saltenvs" ];then
            SALT_BOOT_ONLY_INSTALL_SALT="yes"
            argmatch="1"
        fi
        if [ "x${1}" = "x--only-nodetype" ];then
            DO_NODETYPE="y"
            DO_SALT="no"
            DO_MASTERSALT="no"
            argmatch="1"
        fi
        if [ "x${1}" = "x--only-salt" ];then
            DO_SALT="y"
            DO_NODETYPE="no"
            DO_MASTERSALT="no"
            argmatch="1"
        fi
        if [ "x${1}" = "x--only-mastersalt" ];then
            DO_MASTERSALT="y"
            DO_NODETYPE="no"
            DO_SALT="no"
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
        if [ "x${1}" = "x--no-nodetype" ];then
            DO_NODETYPE="no"
            argmatch="1"
        fi
        if [ "x${1}" = "x--no-salt" ];then
            FORCE_IS_SALT="no"
            DO_SALT="no"
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
            DO_MASTERSALT="no"
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
            FORCE_SALT_NODETYPE="${2}";
            sh="2";
            argmatch="1"
        fi
        if [ "x${1}" = "x--salt-url" ];then
            SALT_URL="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--salt-branch" ];then
            SALT_BRANCH="${2}";sh="2";argmatch="1"
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
            MS_BRANCH="${2}";sh="2";argmatch="1"
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

setup() {
    detect_os
    set_progs
    parse_cli_opts $LAUNCH_ARGS
    set_vars # real variable affectation
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

check_alive() {
    if [ -e "${ALIVE_MARKER}" ];then
        return
    fi
    restart_modes=""
    kill_old_syncs
    setup_virtualenvs >/dev/null
    # kill all check alive
    ps_etime|sort -n -k2|egrep "boot-salt.*alive"|grep -v grep|while read psline;
    do
        seconds="$(echo "${psline}"|awk '{print $2}')"
        pid="$(filter_host_pids $(echo ${psline}|awk '{print $1}'))"
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
        seconds="$(echo "${psline}"|awk '{print $2}')"
        pid="$(filter_host_pids $(echo ${psline}|awk '{print $1}'))"
        if [ "x${pid}" != "x" ] && [ "${seconds}" -gt "$((60*60*12))" ];then
            bs_log "Something went wrong with last restart(mastersalt), killing old salt call process: ${pid}"
            bs_log "${psline}"
            killall_local_mastersalt_masters
            killall_local_mastersalt_minions
        fi
    done
    ps_etime|sort -n -k2|egrep "salt-call"|grep -v mastersalt|grep -v grep|while read psline;
    do
        seconds="$(echo "${psline}"|awk '{print $2}')"
        pid="$(filter_host_pids $(echo ${psline}|awk '{print $1}'))"
        if [ "x${pid}" != "x" ] && [ "${seconds}" -gt "$((60*60*12))" ];then
            bs_log "Something went wrong with last restart(salt), killing old salt call process: ${pid}"
            bs_log "${psline}"
            killall_local_masters
            killall_local_minions
        fi
    done
    # kill all old (master)salt ping call (> 120 sec)
    ps_etime|sort -n -k2|egrep "salt-call"|grep test.ping|grep mastersalt|grep -v grep|while read psline;
    do
        seconds="$(echo "${psline}"|awk '{print $2}')"
        pid="$(filter_host_pids $(echo $psline|awk '{print $1}'))"
        if [ "x${pid}" != "x" ] && [ "${seconds}" -gt "$((60*2))" ];then
            bs_log "MasterSalt PING stalled, killing old salt call process: ${pid}"
            bs_log "${psline}"
            kill -9 "${pid}"
            killall_local_mastersalt_masters
            killall_local_mastersalt_minions
        fi
    done
    ps_etime|sort -n -k2|egrep "salt-call"|grep test.ping|grep -v mastersalt|grep -v grep|while read psline;
    do
        seconds="$(echo "${psline}"|awk '{print $2}')"
        pid="$(filter_host_pids $(echo ${psline}|awk '{print $1}'))"
        if [ "x${pid}" != "x" ] && [ "${seconds}" -gt "$((60*2))" ];then
            bs_log "Salt PING stalled, killing old salt call process: ${pid}"
            bs_log "${psline}"
            kill -9 "${pid}"
            killall_local_masters
            killall_local_minions
        fi
    done
    start_missing_or_dead
    # ping masters if we are not already forcing restart
    if [ "x${alive_mode}" != "xrestart" ];then
        if [ "x${IS_SALT}" != "x" ];then
            if ! salt_ping_test;then
                if [ "x${IS_SALT_MASTER}" != "x" ];then
                    killall_local_masters
                fi
                killall_local_minions
            fi
        fi
        if [ "x${IS_MASTERSALT}" != "x" ];then
            if ! mastersalt_ping_test;then
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

synchronize_code() {
    restart_modes=""
    kill_old_syncs
    setup_and_maybe_update_code "${SALT_BOOT_SYNC_DEPS}"
    exit_status=0
    if [ "x${QUIET}" = "x" ];then
        bs_log "Code updated"
    fi
    if [ "x${1}" != "xno_refresh" ];then
        if [ "x${DO_SALT}" != "xno" ] &&\
            [ "x${IS_SALT_MINION}" != "x" ] &&\
            [ "x$(get_local_salt_mode)" = "xremote" ];then
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
    fi
}

set_dns_minionid() {
    totest=$1
    shift
    eprefix=$@
    if [ "x${totest}" != "x" ];then
        if [ "x$(cat "${eprefix}/minion_id" 2>/dev/null|${SED} -e "s/ //")" != "x${HOST}" ];then
            if [ ! -d "${eprefix}" ];then
                mkdir -p "${eprefix}"
            fi
            echo "${HOST}" > "${eprefix}"/minion_id
        fi
    fi
}

set_dns() {
    if [ "x$(get_mastersalt)" != "x" ];then
        if [ "x$(cat /etc/hostname 2>/dev/null|${SED} -e "s/ //")" != "x${HOST}" ];then
            bs_log "Resetting hostname file to ${HOST}"
            echo "${HOST}" > /etc/hostname
        fi
        if [ "x$(hostname)" != "x${HOST}" ];then
            bs_log "Resetting hostname to ${HOST}"
            hostname "${HOST}"
        fi
        set_dns_minionid "${IS_SALT}" "${CONF_PREFIX}"
        set_dns_minionid "${IS_MASTERSALT}" "${MCONF_PREFIX}"
        if ! egrep -q "127.*${NICKNAME_FQDN}" /etc/hosts;then
            bs_log "Adding new core hostname alias to localhost"
            echo "127.0.0.1 ${NICKNAME_FQDN}">/tmp/hosts
            cat /etc/hosts>>/tmp/hosts
            echo "127.0.0.1 ${NICKNAME_FQDN}">>/tmp/hosts
            if [ -f /tmp/hosts ];then
                # do not use cp for docker  or any LAYERED FS shadowing compatiblity
                cat /tmp/hosts > /etc/hosts
                rm -f /tmp/hosts
            fi
        fi
        if hash -r domainname 2>/dev/null ;then
            if [ "x$(domainname)" != "x${DOMAINNAME}" ];then
                bs_log "Resetting domainname to ${DOMAINNAME}"
                domainname "${DOMAINNAME}"
            fi
        fi
    fi
}

initial_highstates() {
    ret=${?}
    if [ "x$(get_conf initial_highstate)" != "x1" ];then
        run_highstates
        ret="${?}"
        # on failure try to sync code & redo
        if [ "x${ret}" != "x0" ];then
            SALT_BOOT_SKIP_CHECKOUTS=""
            synchronize_code && run_highstates
            ret="${?}"
        fi
        if [ "x${ret}" = "x0" ];then
            store_conf initial_highstate 1
        fi
    fi
    exit ${ret}
}

cleanup_execlogs() {
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
    if which systemctl 2>/dev/null 1>/dev/null;then
        systemctl disable "${1}".service
    fi
}

enable_service() {
    i="${1}"
    if [ -e "/etc/init/${i}.override" ];then
        rm -f "/etc/init/${i}.override"
    elif [  -e /etc/init.d/${i} ] && [ "x$(which update-rc.d 2>/dev/null)" != "x" ];then
        update-rc.d -f "${i}" defaults 99
    fi
    if which systemctl 2>/dev/null 1>/dev/null;then
        systemctl enable "${1}".service
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
    setup
    MS_EXIT_STATUS=0

    if [ "x$(dns_resolve localhost)" = "x${DNS_RESOLUTION_FAILED}" ];then
        die "${DNS_RESOLUTION_FAILED}"
    fi
    do_install="1"
    if [ "x${SALT_BOOT_KILL}" != "x" ];then
        kill_ms_daemons
        do_install=""
    fi
    if [ "x${SALT_BOOT_CLEANUP}" != "x" ];then
        cleanup_execlogs
        do_install=""
    fi
    if [ "x${SALT_BOOT_CHECK_ALIVE}" != "x" ];then
        check_alive
        do_install=""
    fi
    if [ "x${SALT_BOOT_INITIAL_HIGHSTATE}" != "x" ] \
        && [ x"$(get_conf initial_highstate)" = "x1" ];then
        do_install=""
    fi
    if [ "x${SALT_BOOT_SYNC_CODE}" != "x" ];then
        install_prerequisites
        synchronize_code no_refresh
        do_install=""
    elif [ "x${DO_REFRESH_MODULES}" != "x" ];then
        install_prerequisites
        synchronize_code
        do_install=""
    fi
    if [ "x${FORCE_GIT_PACK}" = "x1" ];then
        git_pack
        if [ "x${ONLY_GIT_PACK}" = "x1" ];then
            MS_EXIT_STATUS="$?"
            do_install=""
        fi
    fi
    if [ "x${SALT_BOOT_RESTART_MINIONS}" != "x" ];then
        restart_local_minions
        restart_local_mastersalt_minions
        do_install=""
    fi
    if [ "x${SALT_BOOT_RESTART_MASTERS}" != "x" ];then
        restart_local_masters
        restart_local_mastersalt_masters
        do_install=""
    fi
    if [ "x${SALT_BOOT_RESTART_DAEMONS}" != "x" ];then
        restart_daemons
        do_install=""
    fi
    if [ "x${do_install}" != "x" ];then
        recap
        set_dns
        install_prerequisites
        synchronize_code
        setup_virtualenvs
        MS_EXIT_STATUS=$?
        if [ "x${SALT_BOOT_ONLY_PREREQS}" = "x" ];then
            create_salt_skeleton
            install_nodetype
            install_mastersalt_env
            install_salt_env
            MS_EXIT_STATUS=$?
            if [ "x${SALT_BOOT_ONLY_INSTALL_SALT}" = "x" ];then
                if [ "x${SALT_BOOT_INITIAL_HIGHSTATE}" != "x" ];then
                    initial_highstates
                else
                    run_highstates
                fi
            fi
            postinstall
        fi
    fi
    exit $MS_EXIT_STATUS
fi
## vim:set et sts=5 ts=4 tw=0:

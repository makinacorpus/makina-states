#!/usr/bin/env bash
# SEE MAKINA-STATES DOCS FOR FURTHER INSTRUCTIONS
#
#    - https://github.com/makinacorpus/makina-states
#
# BOOTSTRAP MAKINA-STATES & SALT ON A DEBIAN / UBUNTU MACHINE FOR
# - install prerequisites
# - configure makina-states for operation in /srv/makina-states (default)
#
# Toubleshooting:
# - If the script fails, just relaunch it and it will continue where it was
# - You can safely relaunch it but be ware that it kills the salt daemons upon configure & setup
#   and consequently not safe for putting directly in salt states (with a cmd.run).
#

get_abspath() {
    PYTHON="$(which python 2>/dev/null)"
    if [ ! -f "${PYTHON}" ]; then
        n=$(basename "${1}")
        cd "$(dirname ${1})"
        echo "${PWD}/${n}"
        cd - > /dev/null
    else
        "${PYTHON}" << EOF
import os
print os.path.abspath("${1}")
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
if [ -h "${0}" ]; then
    THIS="$(readlink -f "${0}")"
else
    THIS="$(get_abspath "${0}")"
fi
LAUNCH_ARGS=${@}
DNS_RESOLUTION_FAILED="dns resolution failed"
ERROR_MSG="There were errors"
RED="\\e[0;31m"
CYAN="\\e[0;36m"
YELLOW="\\e[0;33m"
NORMAL="\\e[0;0m"
SALT_BOOT_DEBUG="${SALT_BOOT_DEBUG:-}"
SALT_BOOT_DEBUG_LEVEL="${SALT_BOOT_DEBUG_LEVEL:-all}"
VALID_BRANCHES=""
VALID_CHANGESETS=""
PATH="${PATH}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"

export PATH

is_container() {
    if cat -e /proc/1/cgroup 2>/dev/null|egrep -q 'docker|lxc'; then
        echo "0"
    else
        echo "1"
    fi
}

filter_host_pids() {
    pids=""
    if [ "x$(is_container)" = "x0" ]; then
        pids="${pids} $(echo "${@}")"
    else
        for pid in ${@};do
            if [ "x$(grep -q /lxc/ /proc/${pid}/cgroup 2>/dev/null;echo "${?}")" != "x0" ]; then
                pids="${pids} $(echo "${pid}")"
            fi
         done
    fi
    echo "${pids}" | sed -e "s/\(^ \+\)\|\( \+$\)//g"
}

set_progs() {
    UNAME="${UNAME:-"$(uname | awk '{print tolower($1)}')"}"
    SED=$(which sed)
    if [ "x${UNAME}" != "xlinux" ]; then
        SED=$(which gsed)
    fi
    GETENT="$(which getent 2>/dev/null)"
    PERL="$(which perl 2>/dev/null)"
    PYTHON="$(which python2.7 2>/dev/null)"
    if [ "x${PYTHON}" = "x" ]; then
        PYTHON="$(which python 2>/dev/null)"
    fi
    BHOST="$(which host 2>/dev/null)"
    DIG="$(which dig 2>/dev/null)"
    NSLOOKUP="$(which nslookup 2>/dev/null)"
    PS="$(which ps)"
    NC=$(which nc 2>/dev/null)
    NETCAT=$(which netcat 2>/dev/null)
    if [ ! -e "${NC}" ]; then
        if [ -e "${NETCAT}" ]; then
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
    if [ "x$SALT_BOOT_DEBUG" != "x" ]; then
        bs_log ${@}
    fi
}

# X: connection failure
# 0: connection success
check_connectivity() {
    ip=${1}
    tempo="${3:-1}"
    port=${2}
    ret="0"
    if [ -e "${NC}" ]; then
        while [ "x${tempo}" != "x0" ];do
            tempo="$((${tempo} - 1))"
            # one of
            # Connection to 127.0.0.1 4506 port [tcp/*] succeeded!
            # foo [127.0.0.1] 4506 (?) open
            ret=$(${NC} -w 5 -v -z ${ip} ${port} 2>&1|egrep -q "open$|Connection.*succeeded";echo ${?})
            if [ "x${ret}" = "x0" ]; then
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
    if [ "x${ret}" != "x0" ]; then
        die_ "${ret}" "${msg}"
    fi
}

die_in_error() {
    die_in_error_ "${?}" "${@}"
}

test_online() {
    ping -W 10 -c 1 8.8.8.8 1>/dev/null 2>/dev/null
    if [ "x${?}" = "x0" ] || [ "x${TRAVIS}" != "x" ]; then
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
        if [ "x${i}" != "x" ]; then
            resolvers="${resolvers} ${i}"
        fi
    done
    for resolver in ${resolvers};do
        if echo ${resolver} | grep -q hostsv4; then
            res=$(${GETENT} ahostsv4 ${ahost}|head -n1 2>/dev/null| awk '{ print $1 }')
        elif echo ${resolver} | grep -q hostsv6; then
            res=$(${GETENT} ahostsv6 ${ahost}|head -n1 2>/dev/null| awk '{ print $1 }')
        elif echo ${resolver} | grep -q dig; then
            res=$(${resolver} ${ahost} 2>/dev/null| awk '/^;; ANSWER SECTION:$/ { getline ; print $5 }')
        elif echo ${resolver} | grep -q nslookup; then
            res=$(${resolver} ${ahost} 2>/dev/null| awk '/^Address: / { print $2  }')
        elif echo ${resolver} | grep -q python; then
            res=$(${resolver} -c "import socket;print socket.gethostbyname('${ahost}')" 2>/dev/null)
        elif echo ${resolver} | grep -q perl; then
            res=$(${resolver} -e "use Socket;\$packed_ip=gethostbyname(\"${ahost}\");print inet_ntoa(\$packed_ip)")
        elif echo ${resolver} | grep -q getent; then
            res=$(${resolver} ahosts ${ahost}|head -n1 2>/dev/null| awk '{ print $1 }')
        fi
        # do not accet ipv6 resolutions
        thistest="$(echo "${res}"|grep -q ":";echo ${?})"
        if [ "x${thistest}" = "x0" ]; then res="";fi
        if [ "x${res}" != "x" ]; then
            break
        fi
    done
    if [ "x${res}" = "x" ]; then
        die "${DNS_RESOLUTION_FAILED}"
    fi
    echo ${res}
}

# set environment variables determining the underlying os
detect_os() {
    # make as a function to be copy/pasted as-is in multiple scripts
    set_progs
    UNAME="${UNAME:-"$(uname | awk '{print tolower($1)}')"}"
    DISTRIB_CODENAME=""
    DISTRIB_ID=""
    DISTRIB_BACKPORT=""
    if hash -r lsb_release >/dev/null 2>&1; then
        DISTRIB_ID=$(lsb_release -si)
        DISTRIB_CODENAME=$(lsb_release -sc)
        DISTRIB_RELEASE=$(lsb_release -sr)
    else
        echo "unespected case, no lsb_release"
        exit 1
    fi
    if [ "x${DISTRIB_ID}" = "xDebian" ]; then
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

get_chrono() {
    date "+%F_%H-%M-%S"
}

get_full_chrono() {
    date "+%F_%H-%M-%S-%N"
}

set_colors() {
    if [ "x${NO_COLORS}" != "x" ]; then
        YELLOW=""
        RED=""
        CYAN=""
        NORMAL=""
    fi
}

get_conf(){
    key="${1}"
    echo $(cat "${SALT_MS}/etc/makina-states/$key" 2>/dev/null)
}

store_conf(){
    key="${1}"
    val="${2}"
    echo "${val}">"${SALT_MS}/etc/makina-states/${key}"
}

get_default_knob() {
    key="${1}"
    stored_param="$(get_conf ${key})"
    cli_param="${2}"
    default="${3:-}"
    if [ "x${cli_param}" != "x" ]; then
        setting="${cli_param}"
    elif [ "x${stored_param}" != "x" ]; then
        setting="${stored_param}"
    else
        setting="${default}"
    fi
    if [ "x${stored_param}" != "x${setting}" ]; then
        store_conf ${key} "${setting}"
    fi
    echo "${setting}"
}

get_minion_id() {
    confdir="${1:-"${CONF_PREFIX}"}"
    notfound=""
    mmid="${SALT_MINION_ID:-}"
    if [ "x${mmid}" = "x" ] ;then
        if [ -f "${confdir}/minion_id" ]; then
            mmid=$(cat "${confdir}/minion_id" 2> /dev/null)
        elif egrep -q "^id: [^ ]+" "$confdir/minion" "${confdir}/minion.d/"*conf 2>/dev/null; then
            mmid=$(egrep -r "^id:" "$confdir/minion" "${confdir}/minion.d/"*conf 2>/dev/null|\
                tail -n1|awk '{print $2}'|grep -v __MS_MINIONID__)
        else
            mmid=$(hostname -f)
        fi
    fi
    if [ "x${mmid}" = "x" ]; then
        mmid="${2:-$(hostname -f)}"
    fi
    echo $mmid
}

set_valid_upstreams() {
    if [ "x${SETTED_VALID_UPSTREAM}" != "x" ]; then
        return
    fi
    if [ ! -e "$(which git 2>/dev/null)" ]; then
        VALID_BRANCHES="stable v2"
    fi
    if [ "x${VALID_BRANCHES}" = "x" ]; then
        if [ -e "${SALT_MS}/.git/config" ]; then
            SETTED_VALID_UPSTREAM="1"
            VALID_BRANCHES="${VALID_BRANCHES} $(echo $(cd "${SALT_MS}" && git branch| cut -c 3-))"
            VALID_CHANGESETS="${VALID_CHANGESETS} $(echo $(cd "${SALT_MS}" && git log --pretty=format:'%h %H'))"

        fi
    fi
    # remove \n
    VALID_BRANCHES=$(echo $(echo "${VALID_BRANCHES}"|tr -s "[:space:]" "\\n"|sort -u))
    VALID_CHANGESETS=$(echo $(echo "${VALID_CHANGESETS}"|tr -s "[:space:]" "\\n"|sort -u))
}

validate_changeset() {
    set_valid_upstreams
    msb="${1}"
    ret=""
    # also add if we had a particular changeset saved in conf
    # remove
    if [ "x${msb}" != "x" ]; then
        c="$(sanitize_changeset ${msb})"
        thistest="$(echo "${VALID_CHANGESETS}" "${VALID_BRANCHES}" | grep -q "${c}";echo "${?}")"
        if [ "x${thistest}" = "x0" ]; then
            ret="${msb}"
        fi

    fi
    # if we pin a particular changeset make hat as a valid branch
    if [ "x${ret}" = "x" ]; then
        if [ -e "${SALT_MS}/.git" ]; then
            thistest="$(cd "${SALT_MS}" && git log "${msb}" 2>/dev/null 1>/dev/null;echo ${?})"
            if [ "x${thistest}" = "x0" ]; then
                ret="${msb}"
                break
            fi
        fi
    fi
    if [ "x${ret}" != "x" ]; then
       echo "${ret}"
    fi
}

get_salt_url() {
    get_default_knob salt_url "${SALT_URL}" "https://github.com/makinacorpus/salt.git"
}

get_salt_branch() {
    get_default_knob salt_branch "${SALT_BRANCH}" "2015.8"
}

get_ansible_url() {
    get_default_knob ansible_url "${ANSIBLE_URL}" "https://github.com/makinacorpus/ansible.git"
}

get_ansible_branch() {
    get_default_knob ansible_branch "${ANSIBLE_BRANCH}" "stable-2.0.0.1"
}

get_ms_url() {
    get_default_knob ms_url "${MS_URL}" "https://github.com/makinacorpus/makina-states.git"
}

get_ms_branch() {
    set_valid_upstreams
    DEFAULT_MS_BRANCH="v2"
    vmsb=""
    for msb in "${MS_BRANCH}" "$(get_conf ms_branch)";do
        cmsb="$(validate_changeset ${msb})"
        if [ "x${cmsb}" != "x" ]; then
            vmsb="${cmsb}"
            break
        fi
    done
    if [ "x${vmsb}" = "x" ]; then
        vmsb="${DEFAULT_MS_BRANCH}"
    fi
    echo "${vmsb}"
}

validate_nodetype() {
    n="${1}"
    nodetypes="devhost|dockercontainer|kvm|laptop|lxccontainer|server|scratch|travis|vagrantvm|vm"
    if [ "x${n}" != "x" ]; then
        # at first we may have download just the bootsalt script, fallback on well known nodetypes
        if [ ! -e "${SALT_MS}/salt/makina-states/nodetypes/${n}.sls" ]; then
            # invalid nodetype, use default
            if ! echo "${n}" | egrep -q "${nodetypes}"; then
               n=""
            fi
        fi
    fi
    echo "${n}"
}

get_default_nodetype() {
    if [ "x${TRAVIS}" != "x" ]; then
        DEFAULT_NT="travis"
    else
        DEFAULT_NT="scratch"
    fi
    echo "$(validate_nodetype ${DEFAULT_NT})"
}

get_nodetype() {
    get_default_knob nodetype "$(validate_nodetype ${SALT_NODETYPE})" "$(get_default_nodetype)"
}

set_vars() {
    set_colors
    QUIET=${QUIET:-}
    RELEASE_URL="${RELEASE_URL:-https://github.com/makinacorpus/makina-states/releases/download/attachedfiles}"
    VENV_URL="${VENV_URL:-"${RELEASE_URL}/virtualenv-makina-states-${DISTRIB_ID}-${DISTRIB_CODENAME}-v2.tar.xz"}"
    PREFIX="${PREFIX:-/srv}"
    SALT_MS="${PREFIX}/makina-states"
    SALT_PILLAR="${SALT_MS}/pillar"
    CHRONO="$(get_chrono)"
    TRAVIS_DEBUG="${TRAVIS_DEBUG:-}"
    TMPDIR="${TMPDIR:-"/tmp"}"
    BASE_PACKAGES="python-software-properties curl python-virtualenv git rsync bzip2"
    BASE_PACKAGES="${BASE_PACKAGES} acl build-essential m4 libtool pkg-config autoconf gettext"
    BASE_PACKAGES="${BASE_PACKAGES} groff man-db automake tcl8.5 debconf-utils swig"
    BASE_PACKAGES="${BASE_PACKAGES} libsigc++-2.0-dev libssl-dev libgmp3-dev python-dev"
    BASE_PACKAGES="${BASE_PACKAGES} libffi-dev libzmq3-dev libmemcached-dev"
    NO_MS_VENV_CACHE="${NO_MS_VENV_CACHE:-"no"}"
    DO_INSTALL_PREREQUISITES="${DO_INSTALL_PREREQUISITES:-"y"}"
    DO_ONLY_SYNC_CODE="${DO_ONLY_SYNC_CODE:-"no"}"
    DO_SYNC_CODE="${DO_SYNC_CODE:-"y"}"
    DO_GIT_PACK="${DO_GIT_PACK:-"no"}"
    DO_SETUP_VIRTUALENV="${DO_SETUP_VIRTUALENV:-"y"}"
    DO_INSTALL_NODETYPE="${DO_INSTALL_NODETYPE:-"y"}"
    DO_RECONFIGURE_SALT="${DO_RECONFIGURE_SALT:-"y"}"
    DO_INSTALL_MAKINASTATES="${DO_INSTALL_MAKINASTATES:-"y"}"
    DO_NOCONFIRM="${DO_NOCONFIRM:-}"
    VENV_PATH="${VENV_PATH:-"${SALT_MS}/venv"}"
    EGGS_GIT_DIRS="ansible salt salttesting"
    PIP_CACHE="${VENV_PATH}/cache"
    CONF_PREFIX="${SALT_MS}/etc/salt"
    # nodetypes (calculed now in get_nodetype) and controllers sls
    # salt variables
    # global installation marker
    # base sls bootstrap
    bootstrap_pref="makina-states"
    bootstrap_nodetypes_pref="${bootstrap_pref}.nodetypes"
    bootstrap_controllers_pref="${bootstrap_pref}.controllers"
    salt_bootstrap_nodetype="${bootstrap_nodetypes_pref}.$(get_nodetype)"
    salt_bootstrap_controller="${bootstrap_controllers_pref}.salt"
    SALT_MINION_ID="${SALT_MINION_ID:-}"
    set_valid_upstreams
    # just tell to bootstrap and run highstates
    if [ "x${QUIET}" = "x" ]; then
        QUIET_GIT=""
    else
        QUIET_GIT="-q"
    fi
    # try to get a released version of the virtualenv to speed up installs
    declare -A VENV_URLS_MD5
    VENV_URLS_MD5[a${RELEASE_URL}/virtualenv-makina-states-ubuntu-vivid-stable.tar.xz]="940c8d19e6b7d25dffb091634ddf629a"
    VENV_URLS_MD5[a${RELEASE_URL}/virtualenv-makina-states-ubuntu-trusty-stable.tar.xz]="4a8a83c02846770b4686b4b01b9b8e18"
    VENV_MD5=${VENV_MD5:-${VENV_URLS_MD5[${VENV_URL}]}}
    # export variables to support a restart
    export MS_URL="$(get_ms_url)"
    export MS_BRANCH="$(get_ms_branch)"
    export SALT_URL="$(get_salt_url)"
    export SALT_BRANCH="$(get_salt_branch)"
    export ANSIBLE_URL="$(get_ansible_url)"
    export ANSIBLE_BRANCH="$(get_ansible_branch)"
    #
    export BASE_PACKAGES VENV_URL VENV_MD5 VENV_URLS_MD5 NO_MS_VENV_CACHE
    #
    export DO_INSTALL_MAKINASTATES DO_INSTALL_NODETYPE DO_SKIP_HIGHSTATE
    export DO_NOCONFIRM DO_GIT_PACK DO_SYNC_CODE DO_SKIP_CHECKOUTS
    export DO_INSTALL_PREREQUISITES DO_ONLY_SYNC_CODE DO_SETUP_VIRTUALENV
    #
    export TRAVIS_DEBUG TRAVIS QUIET
    #
    export PREFIX VENV_PATH PIP_CACHE SALT_MS SALT_MINION_ID
}

check_py_modules() {
    # test if salt binaries are there & working
    bin="${VENV_PATH}/bin/python"
    "${bin}" << EOF
import ansible
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

recap_(){
    need_confirm="${1}"
    debug="${2:-$SALT_BOOT_DEBUG}"
    bs_yellow_log "----------------------------------------------------------"
    bs_yellow_log " MAKINA-STATES BOOTSTRAPPER (@$(get_ms_branch)) FOR $DISTRIB_ID"
    bs_yellow_log "   - ${THIS} [--help] [--long-help]"
    bs_yellow_log "----------------------------------------------------------"
    bs_log "  Minion Id: $(get_minion_id)"
    bs_log "DATE: ${CHRONO}"
    bs_log "SALT_NODETYPE: $(get_nodetype)"
    bs_log "PREFIX: ${PREFIX}"
    bs_yellow_log "---------------------------------------------------"
    if [ "x${need_confirm}" != "xno" ] && [ "x${DO_NOCONFIRM}" = "x" ]; then
        bs_yellow_log "To not have this confirmation message, do:"
        bs_yellow_log "    export DO_NOCONFIRM='1'"
    fi
}

recap() {
    will_do_recap="x"
    if [ "x${SALT_BOOT_CHECK_ALIVE}" != "x" ]; then
        will_do_recap=""
    fi
    if [ "x${QUIET}" != "x" ]; then
        will_do_recap=""
    fi
    if [ "x${will_do_recap}" != "x" ]; then
        recap_
        travis_sys_info
    fi
    recap_ "no" "y" > "${TMPDIR}/boot_salt_top"
}

is_apt_installed() {
    if ! dpkg-query -s ${@} 2>/dev/null|egrep "^Status:"|grep -q installed; then
        return 1
    fi
}

lazy_apt_get_install() {
    MS_WITH_PKGMGR_UPDATE=${MS_WITH_PKGMGR_UPDATE:-}
    to_install=""
    for i in ${@};do
         if ! is_apt_installed ${i}; then
             to_install="${to_install} ${i}"
         fi
    done
    if [ "x${to_install}" != "x" ]; then
        bs_log "Installing ${to_install}"
        if [ "x${MS_WITH_PKGMGR_UPDATE}" != "x" ]; then
            apt-get update
        fi
        apt-get install -y --force-yes ${to_install}
    fi
}

setup_backports() {
    # on ubuntu enable backports (saucy) release repos, & on debian just backport
    # saucy is now on archives !
    if [ "x${DISTRIB_BACKPORT}" != "x" ] && greq -vq "${DISTRIB_BACKPORT}" /etc/apt/sources.list; then
        bs_log "Activating backport from ${DISTRIB_BACKPORT} to ${DISTRIB_CODENAME}"
        cp  /etc/apt/sources.list "/etc/apt/sources.list.${CHRONO}.sav"
        "${SED}" "/^deb.*${DISTRIB_BACKPORT}/d" -i /etc/apt/sources.list
        echo "# backport added by boot-salt">/tmp/aptsrc
        egrep "^deb.* ${DISTRIB_CODENAME} " /etc/apt/sources.list | \
            "${SED}" -i -e "s/${DISTRIB_CODENAME}/${DISTRIB_BACKPORT}/g" \
            > /tmp/aptsrc${CHRONO}
        cat /tmp/aptsrc${CHRONO} >> /etc/apt/sources.list
        rm -f /tmp/aptsrc${CHRONO}
    fi

}

teardown_backports() {
    # deactivated, too much risks
    : noop
}

install_prerequisites() {
    if [ "x${DO_INSTALL_PREREQUISITES}" != "xy" ]; then
        bs_log "prerequisites setup skipped"
        return 0
    fi
    if [ "x${QUIET}" = "x" ]; then
        bs_log "Check package dependencies"
    fi
    MS_WITH_PKGMGR_UPDATE="y" lazy_apt_get_install ${BASE_PACKAGES} \
        || die " [bs] Failed install rerequisites"
}

salt_call_wrapper() {
    last_salt_retcode=-1
    saltargs=" -c ${CONF_PREFIX} --retcode-passthrough"
    if [ "x${SALT_BOOT_DEBUG}" != "x" ]; then
        saltargs="${saltargs} -l${SALT_BOOT_DEBUG_LEVEL}"
    else
        saltargs="${saltargs} -linfo"
    fi
    if [ "x$(get_nodetype)" = "xtravis" ]; then
        touch /tmp/travisrun
        ( while [ -f /tmp/travisrun ];do sleep 15;echo "keep me open";sleep 45;done; )&
    fi
    bs_log "Calling:"
    echo ""\
        "${VENV_PATH}/bin/python ${SALT_MS}/mc_states/saltcaller.py" \
        " --validate-states --no-display-ret --use-vt -v --executable" \
        " ${SALT_MS}/bin/salt-call ${saltargs} ${@}"
    "${VENV_PATH}/bin/python" "${SALT_MS}/mc_states/saltcaller.py" \
        --validate-states --no-display-ret --use-vt -v --executable \
        "${SALT_MS}/bin/salt-call" ${saltargs} ${@}
    last_salt_retcode=${?}
    if [ "x$(get_nodetype)" = "xtravis" ]; then
        rm -f /tmp/travisrun
    fi
    return ${last_salt_retcode}
}

check_restartmarker_and_maybe_restart() {
    if [ "x${SALT_BOOT_IN_RESTART}" = "x" ]; then
        if [ "x${SALT_BOOT_NEEDS_RESTART}" != "x" ]; then
            touch "${SALT_MS}/.bootsalt_need_restart"
        fi
        if [ -e "${SALT_MS}/.bootsalt_need_restart" ] && [ "x${SALT_BOOT_NO_RESTART}" = "x" ]; then
            chmod +x "${SALT_MS}/_scripts/boot-salt.sh"
            export SALT_BOOT_NO_RESTART="1"
            export SALT_BOOT_IN_RESTART="1"
            export DO_NOCONFIRM='1'
            bootsalt="${SALT_MS}/_scripts/boot-salt.sh"
            if [ "x${QUIET}" = "x" ]; then
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
        if [ -e "/var/log/salt/${i}" ]; then
            cat "/var/log/salt/${i}"
        fi
    done
    set +x
}

travis_sys_info() {
    return
    if [ "x$(get_nodetype)" = "xtravis" ] && [ "x${TRAVIS_DEBUG}" != "x" ]; then
        sys_info
    fi
}

get_git_branch() {
    cd "${1}" 1>/dev/null 2>/dev/null
    br="$(git branch | grep "*"|grep -v grep)"
    echo "${br}"|"${SED}" -e "s/\* //g"
    cd - 1>/dev/null 2>/dev/null
}

validadate_git_repo() {
    ret="1"
    for i in branches config HEAD index info objects refs;do
        if [ ! -e "${1}/${i}" ]; then
            ret=""
        fi
    done
    echo "${ret}"
}

get_valid_git_repo() {
    repo="${1}"
    ret=""
    if [ "x${repo}" = "x" ]; then
        repo="${PWD}"
    fi
    if [ "x$(validadate_git_repo "${repo}/.git")" = "x1" ]; then
        ret="${repo}/.git"
    elif [ "x$(validadate_git_repo "${repo}")" = "x1" ]; then
        ret="${repo}"
    fi
    echo "${ret}"
}

get_pack_marker() {
     gmarker="$(get_valid_git_repo "${@}")/curgitpackid"
     if [ "x${gmarker}" != "x/curgitpackid" ]; then
         echo "${gmarker}"
     fi
}

get_pack_marker_value() {
    marker=$(get_pack_marker "${@}")
    if [ "x${marker}" != "x" ]; then
        echo "$(get_curgitpackid "${marker}")"
    else
        echo -1
    fi
}

increment_gitpack_id() {
    repo="$(get_valid_git_repo "${@}")"
    if [ "x${repo}" != "x" ]; then
        marker="$(get_pack_marker "${repo}")"
        echo "$(( $(get_pack_marker_value "${repo}") + 1 ))" > "${marker}"
    fi
}

git_pack_dir() {
    f="${1}"
    cd "${f}/.."
    # pack each 10th call
    git_counter="$(($(get_pack_marker_value) % 10))"
    if [ "x${git_counter}" = "x0" ]; then
        bs_log "Git packing ${f}"
        git prune || /bin/true
        git gc --aggressive || /bin/true
    else
        bs_log "Git packing ${f} skipped (${git_counter}/10)"
    fi
    if [ "x${?}" = "x0" ]; then
        increment_gitpack_id
    fi
}

git_pack() {
    bs_log "Maybe packing git repositories"
    # pack git repositories in salt scope
    find "${SALT_MS}" -name .git -type d|while read f;do
            git_pack_dir "${f}"
    done
}

create_venv_dirs() {
    venv_path="${1:-${VENV_PATH}}"
    if [ ! -e "${venv_path}/src" ]; then
        mkdir -p "${venv_path}/src"
    fi
}

synchronize_code() {
    if [ "x${DO_SYNC_CODE}" != "xy" ]; then
        bs_log "Sync code skipped"
        return 0
    fi
    if [ "x${MS_BRANCH}" != "x" ] && [ "x$(validate_changeset ${MS_BRANCH})" = "x" ]; then
        bs_yellow_log "Valid branches: $(echo ${VALID_BRANCHES})"
        die "Please provide a valid \$MS_BRANCH (or -b \$branch) (inputed: "$(get_ms_branch)")"
    fi
    kill_old_syncs
    ms="${SALT_MS}"
    if [ "x${SALT_BOOT_IN_RESTART}" = "x" ] && test_online && [ "x${SALT_BOOT_SKIP_CHECKOUTS}" = "x" ]; then
        if [ "x${QUIET}" = "x" ]; then
            bs_yellow_log "If you want to skip checkouts, next time do export DO_SKIP_CHECKOUTS=y"
        fi
        if [ ! -d "${ms}/.git" ]; then
            parent="$(dirname ${ms})"
            if [ ! -e "${parent}" ]; then
                mkdir "${parent}"
            fi
            remote="remotes/origin/"
            branch_pref=""
            ms_branch="$(get_ms_branch)"
            thistest="$(echo "${ms_branch}" | grep -q "changeset:";echo "${?}")"
            if [ "x${thistest}" = "x0" ]; then
                ms_branch="$(sanitize_changeset "${ms_branch}")"
                remote=""
                branch_pref="changeset_"
            fi
            git clone ${QUIET_GIT} "$(get_ms_url)" "${ms}" &&\
            cd "${ms}" &&\
            git checkout ${QUIET_GIT} "${remote}""${ms_branch}" -b "${branch_pref}""${ms_branch}" &&\
            cd - 1>/dev/null 2>/dev/null
            SALT_BOOT_NEEDS_RESTART="1"
            if [ "x${?}" = "x0" ]; then
                if [ "x${QUIET}" = "x" ]; then
                    bs_yellow_log "Downloaded makina-states (${ms})"
                fi
            else
                die " [bs] Failed to download makina-states (${ms})"
            fi
        fi
        cd "${ms}"
        create_venv_dirs "${VENV_PATH}"
        if [ ! -e src ]; then
            ln -sf "${VENV_PATH}/src" src
        fi
        if [ ! -e src ]; then
            die " [bs] pb with linking venv in ${ms}"
        fi
        if [ -d src ] && [ ! -h  src ]; then
            die " [bs] pb with linking venv in ${ms} (2)"
        fi
        for i in "${ms}" "${ms}/src/"*;do
            is_changeset=""
            branch_pref=""
            if [ -e "${i}/.git" ]\
                && [ "x${DO_SKIP_CHECKOUTS}" = "x" ]; then
                remote="remotes/origin/"
                co_branch="master"
                pref=""
                if [ "x${i}" = "x${ms}" ]; then
                    co_branch="$(get_ms_branch)"
                    thistest="$(echo "${co_branch}" | grep -q "changeset:";echo "${?}")"
                    if [ "x${thistest}" = "x0" ]; then
                        co_branch="$(sanitize_changeset "${co_branch}")"
                        pref="changeset:"
                        is_changeset="1"
                        branch_pref="changeset_"
                        remote=""
                    fi
                fi
                if  [ "x${i}" = "x${ms}/src/salttesting" ] \
                 || [ "x${i}" = "x${ms}/src/SaltTesting" ]; then
                    co_branch="develop"
                fi
                if [ "x${i}" = "x${ms}/src/ansible" ]; then
                    co_branch="$(get_ansible_branch)"
                fi
                if [ "x${i}" = "x${ms}/src/salt" ]; then
                    co_branch="$(get_salt_branch)"
                fi
                if [ "x${QUIET}" = "x" ]; then
                    bs_log "Upgrading ${i}"
                fi
                cd "${i}"
                git fetch --tags origin 1>/dev/null 2>/dev/null
                git fetch ${QUIET_GIT} origin
                lbranch="$(get_git_branch .)"
                if [ "x${lbranch}" != "x${branch_pref}${co_branch}" ]; then
                    if [ "x$(git branch|egrep " ${co_branch}\$" |wc -l|${SED} -e "s/ //g")" != "x0" ]; then
                        # branch already exists
                        if [ "x${QUIET}" = "x" ]; then
                            bs_log "Switch branch: ${lbranch} -> ${branch_pref}${co_branch}"
                        fi
                        git checkout ${QUIET_GIT} "${branch_pref}""${co_branch}"
                        ret="${?}"
                    else
                        # branch  does not exist yet
                        if [ "x${QUIET}" = "x" ]; then
                            bs_log "Create & switch on branch: ${branch_pref}${co_branch} from ${lbranch}"
                        fi
                        git checkout ${QUIET_GIT} "${remote}""${co_branch}" -b "${branch_pref}""${co_branch}"
                        ret="${?}"
                    fi
                    if [ "x${ret}" != "x0" ]; then
                        die "Failed to switch branch: ${lbranch} -> ${branch_pref}${co_branch}"
                    else
                        if [ "x${QUIET}" = "x" ]; then
                            bs_log "Update is necessary"
                        fi
                        SALT_BOOT_NEEDS_RESTART="1"
                    fi
                else
                    if [ "x${is_changeset}" != "x1" ]; then
                        git diff ${QUIET_GIT} origin/${co_branch} --exit-code 1>/dev/null 2>/dev/null
                        if [ "x${?}" != "x0" ]; then
                            if [ "x${QUIET}" = "x" ]; then
                                bs_log "Update is necessary"
                            fi
                        fi && if \
                            [ "x${i}" = "x${ms}/src/SaltTesting" ] \
                            || [ "x${i}" = "x${ms}/src/salttesting" ] \
                            || [ "x${i}" = "x${ms}/src/docker-py" ]
                        then
                            git reset ${QUIET_GIT} --hard origin/${co_branch}
                            die_in_error "${i} git reset failed"
                        else
                            git merge ${QUIET_GIT} --ff-only origin/${co_branch}
                            die_in_error "${i} merge forward failed"
                        fi
                        SALT_BOOT_NEEDS_RESTART=1
                    fi
                fi
                if [ "x${QUIET}" = "x" ] && echo "${i}" |grep -q ansible; then
                    bs_log "Upgrading ansible submodules"
                    git submodule update --init --recursive
                    die_in_error "${i} submodules upgrade failed"
                fi
                if [ "x${?}" = "x0" ]; then
                    increment_gitpack_id
                    if [ "x${QUIET}" = "x" ]; then
                        bs_yellow_log "Downloaded/updated ${i}"
                    fi
                else
                    die "Failed to download/update ${i}"
                fi
                if [ "x${i}" = "x${ms}" ]; then
                    store_conf ms_branch "${pref}${co_branch}"
                fi
            fi
        done
    fi
    check_restartmarker_and_maybe_restart
    if [ "x${QUIET}" = "x" ]; then
        bs_log "Code updated"
    fi
}

download_file() {
    url="${1}"
    dest="${2}"
    refmd5="${3}"
    bs_log "Downloading & extracting ${url}"
    curl -Lfk "${url}" > "${dest}"
    if [ "x${?}" != "x0" ]; then
        bs_log "download error"
    else
        md5="$(md5sum "${dest}"|awk '{print $1}')"
        if [ "x${refmd5}" != "x" ]; then
            if [ "x${refmd5}" != "x${md5}" ]; then
                bs_log "MD5 verification failed ( ${md5} != ${refmd5})"
                return 1
            fi
        fi
        bs_log "download complete"
    fi

}

setup_virtualenv() {
    if [ "x${DO_SETUP_VIRTUALENV}" != "xy" ]; then
        bs_log "virtualenv setup skipped"
        return 0
    fi
    if [ ! -e "${VENV_PATH}/salt/bin/salt" ]; then
        tmparc="${TMPDIR:-/tmp}/salt.tar.xz"
        # only download if exists
        if [ "x${NO_MS_VENV_CACHE}" = "xy" ]; then
            bs_log "Warn: virtualenv cache forced-off, will rebuild"
        elif curl -kfI ${VENV_URL} >/dev/null 2>&1; then
            if ! download_file "${VENV_URL}" "${tmparc}" "${VENV_MD5}"; then
                bs_log "Archive error, aborting"
                exit 1
            fi
            tar xJf "${tmparc}" -C /
            if [ "x${?}" != "x0" ]; then
                bs_log "extract error"
            else
                bs_log "extract complete"
            fi
            rm -f "${tmparc}"
        else
            bs_log "Warn: virtualenv cache archive not found, will rebuild"
        fi
    fi
    # Script is now running in makina-states git location
    # Check for virtualenv presence
    cd "${SALT_MS}"
    if     [ ! -e "${VENV_PATH}/bin/activate" ] \
        || [ ! -e "${VENV_PATH}/lib" ] \
        || [ ! -e "${VENV_PATH}/include" ] \
        ; then
        bs_log "Creating virtualenv in ${VENV_PATH}"
        if [ ! -e "${PIP_CACHE}" ]; then
            mkdir -p "${PIP_CACHE}"
        fi
        if [ ! -e "${VENV_PATH}" ]; then
            mkdir -p "${VENV_PATH}"
        fi
        virtualenv --system-site-packages --unzip-setuptools ${VENV_PATH} &&\
        . "${VENV_PATH}/bin/activate" &&\
        "${VENV_PATH}/bin/easy_install" -U setuptools &&\
        "${VENV_PATH}/bin/pip" install -U pip &&\
        deactivate
        BUILDOUT_REBOOTSTRAP=y
    fi

    # virtualenv is present, activate it
    if [ -e "${VENV_PATH}/bin/activate" ]; then
        if [ "x${QUIET}" = "x" ]; then
            bs_log "Activating virtualenv in ${VENV_PATH}"
        fi
        . "${VENV_PATH}/bin/activate"
    fi
    create_venv_dirs "${VENV_PATH}"
    # install requirements
    cd "${SALT_MS}"
    install_git=""
    for i in ${EGGS_GIT_DIRS};do
        if [ ! -e "${VENV_PATH}/src/${i}" ]; then
            install_git="x"
        fi
    done
    uflag=""
    if check_py_modules; then
        bs_log "Pip install in place"
    else
        bs_log "Python install incomplete"
        if pip --help | grep -q download-cache; then
            copt="--download-cache"
        else
            copt="--cache-dir"
        fi
        pip install -U $copt "${PIP_CACHE}" -r requirements/requirements.txt
        die_in_error "requirements/requirements.txt doesnt install"
        if [ "x${install_git}" != "x" ]; then
            ${SED} -r \
                -e "s#^\# (-e.*__(SALT|ANSIBLE))#\1#g" \
                -e "s#__SALT_URL__#$(get_salt_url)#g" \
                -e "s#__SALT_BRANCH__#$(get_salt_branch)#g" \
                -e "s#__ANSIBLE_URL__#$(get_ansible_url)#g" \
                -e "s#__ANSIBLE_BRANCH__#$(get_ansible_branch)#g" \
                requirements/git_requirements.txt.in \
                > requirements/git_requirements.txt
            # salt & docker had bad history for their deps in setup.py
            # we ignore them and manage that ourselves
            pip install -U $copt "${PIP_CACHE}" --no-deps \
                -r requirements/git_requirements.txt
            die_in_error "requirements/git_requirements.txt doesnt install"
        else
            cwd="${PWD}"
            for i in $EGGS_GIT_DIRS;do
                if [ -e "src/${i}/setup.py" ]; then
                    cd "src/${i}"
                    pip install --no-deps -e .
                fi
                cd "${cwd}"
            done
        fi
        pip install --no-deps -e .
        die_in_error "mc_states doesnt install"
    fi
    for i in ${EGGS_GIT_DIRS};do
        i="${venv_path}/src/${i}"
        if [ ! -e "${i}" ]; then
            die "   * ${i} is not present"
        fi
    done
    link_salt_dir "${SALT_MS}" "${VENV_PATH}"
}

link_salt_dir() {
    where="${1}"
    vpath="${2:-${VENV_PATH}}"
    for i in src;do
        if [ ! -e "$i" ]; then
            echo "There is a problem with pip install (${i})!"
            echo "Prerequisites not achieved."
            exit 1
        fi
        origin="${vpath}/${i}"
        linkname=$(echo ${i}|sed -re "s|${vpath}/?||g")
        destination="${where}/${linkname}"
        if [ -d "${destination}" ] && [ ! -h "${destination}" ]; then
            if [ ! -e "${where}/nobackup" ]; then
                mkdir "${where}/nobackup"
            fi
            echo "moving old directory; \"${where}/${linkname}\" to \"${where}/nobackup/${linkname}-$(date "+%F-%T-%N")\""
            mv "${destination}" "${where}/nobackup/${linkname}-$(date "+%F-%T-%N")"
        fi
        do_link="1"
        if [ -h "${destination}" ]; then
            if [ "x$(readlink ${destination})" = "x${origin}" ]; then
                do_link=""
            else
                rm -v "${destination}"
            fi
        fi
        if [ "x${do_link}" != "x" ]; then
            ln -sfv "${origin}" "${destination}"
        fi
    done
}

reconfigure_salt() {
    if [ "x${DO_RECONFIGURE_SALT}" != "xy" ]; then
        bs_log "salt reconfiguration skipped"
        return 0
    fi
    overwrite="
    ${CONF_PREFIX}/minion.d/01_local.conf
    "
    confs="
    ${CONF_PREFIX}/minion.d/01_local.conf.in:${CONF_PREFIX}/minion.d/01_local.conf
    "
    # configure then salt
    for conft in $confs;do
        conf="$(echo "${conft}"|cut -d: -f2-)"
        template="$(echo "${conft}"|cut -d: -f-1)"
        if [ ! -e "${conf}" ] || ( echo ${overwrite} | grep -q ${conf} );then
            debug_msg "Overwriting ${conf} from ${template}"
            cp -vf "${template}" "${conf}"
        fi
        if egrep -q "__(MS_MINIONID|MS_PREFIX|MS_MS|MS_NODETYPE)__" "${conf}"
        then
            "${SED}" -i -r \
                -e "s/__MS_MINIONID__/$(get_minion_id)/g" \
                -e "s|__MS_PREFIX__|${PREFIX}|g" \
                -e "s|__MS_MS__|${SALT_MS}|g" \
                -e "s|__MS_NODETYPE__|$(get_nodetype)|g" \
                "${conf}" && debug_msg "Reconfigured ${conf}"
        fi
    done
}

is_same() {
    ret=1
    if [ -e "${1}" ] && [ -e "${2}" ]; then
        diff -aq "${1}" "${2}" 1>/dev/null 2>/dev/null
        ret=${?}
    fi
    return ${ret}
}

install_nodetype() {
    if [ "x${DO_INSTALL_NODETYPE}" != "xy" ]; then
        bs_log "Nodetype bootstrap for $(get_nodetype) skipped"
        return 0
    fi
    if [ "x$(get_nodetype)" = "x" ]; then
        bs_yellow_log "Valid nodetypes: $(echo $(\
            ls -1 "${SALT_MS}/salt/makina-states/nodetypes"|\
            egrep -v "standalone|cleanup|init|hooks"|"${SED}" -e "s/.sls//"))"
        die "Please provide a valid nodetype (inputed: \"$(get_nodetype)\")"
    fi
    echo "makina-states.nodetypes.$(get_nodetype): true" >> "${MCONF_PREFIX}/grains"
    if [ "x$(get_nodetype)" != "xscratch" ]; then
        run_salt_bootstrap ${salt_bootstrap_nodetype}
    fi
}

install_makinastates() {
    if [ "x${DO_INSTALL_MAKINASTATES}" != "xy" ]; then
        bs_log "Salt bootstrap for $(get_nodetype) skipped"
        return 0
    fi
    bs_log "Boostrapping salt"
    run_salt_bootstrap "${salt_bootstrap_controller}"
}

get_delay_time() {
    if [ "x$(get_nodetype)" = "xtravis" ]; then
        echo 15
    else
        echo 3
    fi
}

run_salt_bootstrap() {
    bs=${1}
    bs_log "Running ${salt_type} bootstrap: ${bs}"
    if ! salt_call_wrapper state.sls ${bs};then
        echo "${salt_type}: Failed bootstrap: ${bs}"
        exit 1
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
    if [ "x${opt}" = "x" ]; then
        msg="${msg} ${YELLOW}(mandatory)${NORMAL}"
    fi
    if [ "x${default}" != "x" ]; then
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
    bs_yellow_log "This script will install makina-states and maybe configure your host for makina-states operation"
    if [ "x${SALT_LONG_HELP}" != "x" ]; then
        bs_yellow_log "You may need to select the nodetype, and the other informations bits neccesary to"
        bs_yellow_log "desccribe and adapt the behavior to your targeted environment"
        echo
        exemple ":" "install makina-states with default options, without configuring any nodetype"
        exemple " --nodetype=devhost:" "install a saltmaster/minion in 'development' mode"
    fi
    echo
    bs_log "  General settings"
    bs_help "    -h|--help / -l/--long-help" "this help message or the long & detailed one" "" y
    bs_help "    -p|--prefix <path>" "prefix path" "${PREFIX}" yi
    bs_help "    -b|--branch <branch>" "MakinaStates branch to use" "$(get_ms_branch)" y
    bs_help "    -g|--makina-states-url <url>" "makina-states git url" "$(get_ms_url)" y
    bs_help "    --salt-url <url>" "saltstack fork git url" "$(get_salt_url)" y
    bs_help "    --salt-branch <branch>" "saltstack fork git branch" "$(get_salt_branch)" y
    bs_help "    --ansible-url <url>" "saltstack fork git url" "$(get_ansible_url)" y
    bs_help "    --ansible-branch <branch>" "saltstack fork git branch" "$(get_ansible_branch)" y
    bs_help "    -C|--no-confirm" "Do not ask for start confirmation" "" y
    bs_help "    -S|--skip-checkouts" "Skip initial checkouts / updates" "" y
    bs_help "    -s|--skip-highstate" "Skip highstate" "" y
    bs_help "    -d|--debug" "debug/verbose mode" "NOT SET" y
    bs_help "    --debug-level <level>" "debug level (quiet|all|info|error)" "NOT SET" y
    bs_help "    -n|--nodetype <nt>" "Nodetype to install into (devhost | server | dockercontainer | lxcontainer | vm | vagrantvm)" "$(get_nodetype)" "y"
    bs_help "    -m|--minion-id" "Minion id" "$(get_minion_id)" y
    bs_help "    --no-colors" "No terminal colors" "${NO_COLORS}" "y"
    echo
    bs_log "  Actions (no action means install)"
    bs_help "    --synchronize-code" "Only sync sourcecode" "${DO_ONLY_SYNC_CODE}" y
    bs_help "    --no-makina-states" "Do not do base makina-states setup" "${DO_INSTALL_MAKINASTATES}" y
    bs_help "    --no-highstates" "Do not run highstates" "${DO_HIGHSTATES}" y
    bs_help "    --no-prereqs" "Skip prereqs install" "${DO_INSTALL_PREREQUISITES}" y
    bs_help "    --pack" "Do (only) run git pack (gc) if necessary" "${DO_GIT_PACK}" y
    bs_help "    --no-synchronize-code" "Skip sync sourcecode" "${DO_SYNC_CODE}" y
    bs_help "    --no-ms-venv-cache" "Do not try to download prebuilt virtualenvs" "${NO_MS_VENV_CACHE}" y
    bs_help "    --no-nodetype" "Do not run nodetype bootstrap" "${DO_INSTALL_NODETYPE}" y
    bs_help "    --no-venv" "Do not run the virtualenv setup"  "${DO_SETUP_VIRTUALENV}" y
    bs_help "    --no-reconfigure-salt" "Do not touch to salt configuration files" "${DO_RECONFIGURE_SALT}" y
}

parse_cli_opts() {
    #set_vars # to collect defaults for the help message
    args="${@}"
    PARAM=""
    while true
    do
        sh=1
        argmatch=""
        if [ "x${1}" = "x${PARAM}" ]; then
            break
        fi
        if [ "x${1}" = "x-q" ] || [ "x${1}" = "x--quiet" ]; then
            QUIET="1";argmatch="1"
        fi
        if [ "x${1}" = "x-h" ] || [ "x${1}" = "x--help" ]; then
            USAGE="1";argmatch="1"
        fi
        if [ "x${1}" = "x-l" ] || [ "x${1}" = "x--long-help" ]; then
            SALT_LONG_HELP="1";USAGE="1";argmatch="1"
        fi
        if [ "x${1}" = "x-d" ] || [ "x${1}" = "x--debug" ]; then
            SALT_BOOT_DEBUG="y";argmatch="1"
        fi
        if [ "x${1}" = "x--debug-level" ]; then
            SALT_BOOT_DEBUG_LEVEL="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--no-colors" ]; then
            NO_COLORS="1";argmatch="1"
        fi
        if [ "x${1}" = "x-C" ] || [ "x${1}" = "x--no-confirm" ]; then
            DO_NOCONFIRM="y";argmatch="1"
        fi
        if [ "x${1}" = "x--no-ms-venv-cache" ]; then
            NO_MS_VENV_CACHE="y";argmatch="1"
        fi
        if [ "x${1}" = "x--kill" ]; then
            SALT_BOOT_KILL="1"
            argmatch="1"
        fi
        # do not remove yet for retro compat
        if [ "x${1}" = "x--no-prereqs" ]; then
            DO_INSTALL_PREREQUISITES="no"
            argmatch="1"
        fi
        if [ "x${1}" = "x--pack" ]; then
            DO_GIT_PACK="y"
            argmatch="1"
        fi
        if [ "x${1}" = "x--no-synchronize-code" ]; then
            DO_SYNC_CODE="no"
            argmatch="1"
        fi
        if [ "x${1}" = "x--synchronize-code" ]; then
            DO_ONLY_SYNC_CODE="y"
            argmatch="1"
        fi
        if [ "x${1}" = "x--no-venv" ]; then
            DO_SETUP_VIRTUALENV="no"
            argmatch="1"
        fi
        if [ "x${1}" = "x--no-reconfigure-salt" ]; then
            DO_RECONFIGURE_SALT="no"
            argmatch="1"
        fi
        if [ "x${1}" = "x--no-nodetype" ]; then
            DO_INSTALL_NODETYPE="no"
            argmatch="1"
        fi
        if [ "x${1}" = "x--no-makina-states" ]; then
            DO_INSTALL_MAKINASTATES="no"
            argmatch="1"
        fi
        if [ "x${1}" = "x--no-highstates" ]; then
            DO_HIGHSTATES="no"
            argmatch="1"
        fi
        if [ "x${1}" = "x-m" ] || [ "x${1}" = "x--minion-id" ]; then
            SALT_MINION_ID="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-n" ] || [ "x${1}" = "x--nodetype" ]; then
            SALT_NODETYPE="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--salt-url" ]; then
            SALT_URL="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--salt-branch" ]; then
            SALT_BRANCH="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--ansible-url" ]; then
            ANSIBLE_URL="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x--ansible-branch" ]; then
            ANSIBLE_BRANCH="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-g" ] || [ "x${1}" = "x--ms-url" ]; then
            MS_URL="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-b" ] || [ "x${1}" = "x--ms-branch" ]; then
            MS_BRANCH="${2}";sh="2";argmatch="1"
        fi
        if [ "x${1}" = "x-p" ] || [ "x${1}" = "x--prefix" ]; then
            PREFIX="${2}";sh="2";argmatch="1"
        fi
        if [ "x${argmatch}" != "x1" ]; then
            USAGE="1"
            break
        fi
        PARAM="${1}"
        OLD_ARG="${1}"
        for i in $(seq $sh);do
            shift
            if [ "x${1}" = "x${OLD_ARG}" ]; then
                break
            fi
        done
        if [ "x${1}" = "x" ]; then
            break
        fi
    done
    if [ "x${USAGE}" != "x" ]; then
        set_vars
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

ps_etime() {
    ${PS} -eo pid,comm,etime,args | perl -ane '@t=reverse(split(/[:-]/, $F[2])); $s=$t[0]+$t[1]*60+$t[2]*3600+$t[3]*86400;$cmd=join(" ", @F[3..$#F]);print "$F[0]\t$s\t$F[1]\t$F[2]\t$cmd\n"'
}


kill_old_syncs() {
    # kill all stale synchronnise code jobs
    ps_etime|sort -n -k2|egrep "boot-salt.*(synchronize-code)"|grep -v grep|while read psline;
    do
        seconds="$(echo "$psline"|awk '{print $2}')"
        pid="$(filter_host_pids $(echo $psline|awk '{print $1}'))"
        # 8 minutes
        if [ "x${pid}" != "x" ] && [ "${seconds}" -gt "480" ]; then
            bs_log "Something was wrong with last sync, killing old sync processes: $pid"
            bs_log "${psline}"
            kill -9 "${pid}"
        fi
    done
}

run_ms_highstate() {
    bs_log "Running makina-states highstate"
    if ! salt_call_wrapper state.sls makina-states.top; then
        bs_log "Failed highstate"
        return 1
    fi
}

do_highstate() {
    if [ "x${DO_HIGHSTATES}" != "xy" ]; then
        bs_log "salt highstate skipped"
        return 0
    fi
    bs_log "    export DO_HIGHSTATES=no to skip (dangerous)"
    if [ "x$(get_conf initial_highstate)" != "x1" ]; then
        run_ms_highstate
        ret=${?}
        # on failure try to sync code & redo
        if [ "x${ret}" != "x0" ]; then
            export DO_SYNC_CODE="y"
            synchronize_code && run_ms_highstate
            ret=${?}
        fi
        if [ "x${ret}" = "x0" ]; then
            store_conf initial_highstate 1
        fi
        return ${ret}
    else
        run_ms_highstate
    fi
}

main() {
    install_prerequisites &&\
    if [ "x${DO_GIT_PACK}" = "xy" ]; then
        git_pack
        exit $?
    fi &&\
    synchronize_code && \
    if [ "x${DO_ONLY_SYNC_CODE}" = "xy" ]; then
        exit $?
    fi &&\
        setup_virtualenv &&\
        reconfigure_salt &&\
        install_nodetype &&\
        install_makinastates &&\
        do_highstate
}

if [ "x${SALT_BOOT_AS_FUNCS}" = "x" ]; then
    setup
    recap
    if [ "x$(dns_resolve localhost)" = "x${DNS_RESOLUTION_FAILED}" ]; then
        die "${DNS_RESOLUTION_FAILED}"
    fi
    main
fi
exit $?
## vim:set et sts=5 ts=4 tw=0:

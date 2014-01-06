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
LAUNCH_ARGS=$@
get_abspath() {
    python << EOF
import os
print os.path.abspath("$0")
EOF
}

RED="\\033[31m"
CYAN="\\033[36m"
YELLOW="\\033[33m"
NORMAL="\\033[0m"
SALT_BOOT_DEBUG="${SALT_BOOT_DEBUG:-}"
SALT_BOOT_DEBUG_LEVEL="${SALT_BOOT_DEBUG_LEVEL:-all}"
LAUNCHER="$(get_abspath $0)"
DNS_RESOLUTION_FAILED="dns resolution failed"


set_progs() {
    GETENT="$(which getent 2>/dev/null)"
    PERL="$(which perl 2>/dev/null)"
    PYTHON="$(which python 2>/dev/null)"
    HOST="$(which host 2>/dev/null)"
    DIG="$(which dig 2>/dev/null)"
    NSLOOKUP="$(which nslookup 2>/dev/null)"
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
}

bs_log(){
    echo -e "${RED}[bs] ${@}${NORMAL}";
}

bs_yellow_log(){
    echo -e "${YELLOW}[bs] ${@}${NORMAL}";
}

debug_msg() {
    if [[ -n "$SALT_BOOT_DEBUG" ]];then
        bs_log $@
    fi
}

# 1: connection failure
# 0: connection success
check_connectivity() {
    ip=$1
    port=$2
    NC=$(which nc 2>/dev/null)
    NETCAT=$(which netcat 2>/dev/null)
    if [[ ! -e "$NC" ]];then
        if [[ -e "$NETCAT" ]];then
            NC=$NETCAT
        fi
    fi
    if [[ ! -e "$NC" ]];then
        test "$(nc -w 5 -v -z $ip $port 2>&1|egrep 'open$'|wc -l)" != "0";
    fi
    echo $?
}

warn_log() {
    if [[ -e "$SALT_BOOT_CMDFILE" ]] \
        || [[ -e "$SALT_BOOT_OUTFILE" ]] \
        || [[ -e "$SALT_BOOT_LOGFILE" ]];\
    then
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

dns_resolve() {
    ahost="$1"
    set_progs
    resolvers=""
    for i in\
        "$GETENT"\
        "$PERL"\
        "$PYTHON"\
        "$HOST"\
        "$NSLOOKUP"\
        "$DIG";\
    do
        if [[ -n "$i" ]];then
            resolvers="$resolvers $i"
        fi
    done
    if [[ -z "$resolvers" ]];then
        die "$DNS_RESOLUTION_FAILED"
    fi
    res=""
    for resolver in $resolvers;do
        echo $resolver
        case $resolver in
            *host)
                res=$($resolver $ahost 2>/dev/null| awk '/ has address /{ print $4 }')
                ;;
            *dig)
                res=$($resolver $ahost 2>/dev/null| awk '/^;; ANSWER SECTION:$/ { getline ; print $5 }')
                ;;
            *nslookup)
                res=$($resolver $ahost 2>/dev/null| awk '/^Address: / { print $2  }')
                ;;
            *python)
                res=$($resolver -c "import socket;print socket.gethostbyname('$ahost')" 2>/dev/null)
                ;;
            *perl)
                res=$($resolver -e "use Socket;\$packed_ip=gethostbyname(\"$ahost\");print inet_ntoa(\$packed_ip)")
                ;;
            *getent)
                res=$($resolver ahosts $ahost|head -n1 2>/dev/null| awk '{ print $1 }')
                ;;
        esac
        if [[ -n $res ]];then
            break
        fi
    done
    if [[ -z "$res" ]];then
        die "$DNS_RESOLUTION_FAILED"
    fi
    echo $res
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
        if [[ "$DISTRIB_ID" == "Ubuntu" ]];then
            IS_UBUNTU="y"
        fi
    fi
    if [[ -e "$CONF_ROOT/os-release" ]];then
        OS_RELEASE_ID=$(egrep ^ID= $CONF_ROOT/os-release|sed -re "s/ID=//g")
        OS_RELEASE_NAME=$(egrep ^NAME= $CONF_ROOT/os-release|sed -re "s/NAME=""//g")
        OS_RELEASE_VERSION=$(egrep ^VERSION= $CONF_ROOT/os-release|sed -re "s/VERSION=/""/g")
        OS_RELEASE_PRETTY_NAME=$(egrep ^PRETTY_NAME= $CONF_ROOT/os-release|sed -re "s/PRETTY_NAME=""//g")

    fi
    if [[ -e $CONF_ROOT/debian_version ]] && [[ "$OS_RELEASE_ID" == "debian" ]] && [[ "$DISTRIB_ID" != "Ubuntu" ]];then
        IS_DEBIAN="y"
        SALT_BOOT_OS="debian"
        DISTRIB_CODENAME="$(echo $OS_RELEASE_PRETTY_NAME |sed -re "s/.*\((.*)\).*/\1/g")"
    fi
    if [[ $IS_UBUNTU ]];then
        SALT_BOOT_OS="ubuntu"
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

interactive_tempo(){
    tempo="$@"
    tempo_txt="$tempo"
    if [[ $tempo_txt -ge 60 ]];then
        tempo_txt="$(python -c "print $tempo / 60") minute(s)"
    else
        tempo_txt="$tempo second(s)"
    fi
    bs_yellow_log "The installation will continue in $tempo_txt"
    bs_yellow_log "unless you press enter to continue or C-c to abort"
    bs_yellow_log "-------------------  ????  -----------------------"
    read -t $tempo
    bs_yellow_log "Continuing..."
}

get_chrono() {
    date "+%F_%H-%M-%S"
}

set_vars() {
    ROOT="${ROOT:-"/"}"
    CONF_ROOT="${CONF_ROOT:-"${ROOT}etc"}"
    ETC_INIT="${ETC_INIT:-"$CONF_ROOT/init"}"
    detect_os
    set_progs
    HOSTNAME="$(hostname)"
    CHRONO="$(get_chrono)"
    BASE_PACKAGES=""
    BASE_PACKAGES="$BASE_PACKAGES build-essential m4 libtool pkg-config autoconf gettext bzip2"
    BASE_PACKAGES="$BASE_PACKAGES groff man-db automake libsigc++-2.0-dev tcl8.5 python-dev"
    BASE_PACKAGES="$BASE_PACKAGES swig libssl-dev libyaml-dev debconf-utils python-virtualenv"
    BASE_PACKAGES="$BASE_PACKAGES vim git rsync"
    BASE_PACKAGES="$BASE_PACKAGES libzmq3-dev"
    BASE_PACKAGES="$BASE_PACKAGES libgmp3-dev"
    IS_SALT="${IS_SALT:-y}"
    IS_SALT_MASTER="${IS_SALT_MASTER:-y}"
    IS_SALT_MINION="${IS_SALT_MINION:-y}"
    IS_MASTERSALT="${IS_MASTERSALT:-}"
    IS_MASTERSALT_MASTER="${IS_MASTERSALT_MASTER:-}"
    IS_MASTERSALT_MINION="${IS_MASTERSALT_MINION:-}"
    STATES_URL="${STATES_URL:-"https://github.com/makinacorpus/makina-states.git"}"
    PREFIX="${PREFIX:-${ROOT}srv}"
    BIN_DIR="${BIN_DIR:-${ROOT}usr/bin}"
    SALT_PILLAR="${SALT_PILLAR:-$PREFIX/pillar}"
    SALT_BOOT_NOCONFIRM="${SALT_BOOT_NOCONFIRM:-}"
    SALT_ROOT="${SALT_ROOT:-$PREFIX/salt}"
    SALT_BOOT_OUTFILE="${SALT_MS}/.boot_salt.$(get_chrono).out"
    SALT_BOOT_LOGFILE="${SALT_MS}/.boot_salt.$(get_chrono).log"
    SALT_MS="$SALT_ROOT/makina-states"
    MASTERSALT_PILLAR="${MASTERSALT_PILLAR:-$PREFIX/mastersalt-pillar}"
    MASTERSALT_ROOT="${MASTERSALT_ROOT:-$PREFIX/mastersalt}"
    MASTERSALT_MS="$MASTERSALT_ROOT/makina-states"
    TMPDIR="${TMPDIR:-"/tmp"}"
    VENV_PATH="${VENV_PATH:-"/salt-venv"}"
    CONF_PREFIX="${CONF_PREFIX:-"$CONF_ROOT/salt"}"
    MCONF_PREFIX="${MCONF_PREFIX:-"$CONF_ROOT/mastersalt"}"
    # global installation marker
    SALT_BOOT_NOW_INSTALLED=""
    # the current mastersalt.makinacorpus.net hostname
    MASTERSALT_MAKINA_DNS="mastersalt.makina-corpus.net"
    BOOT_LOGS="${SALT_MS}/.bootlogs"
    MBOOT_LOGS="$MASTERSALT_MS/.bootlogs"
    # base sls bootstrap
    bootstrap_pref="makina-states.bootstraps"
    bootstrap_nodetypes_pref="${bootstrap_pref}.nodetypes"
    bootstrap_controllers_pref="${bootstrap_pref}.controllers"

    # nodetypes and controllers sls
    SALT_NODETYPE="${SALT_NODETYPE:-"server"}"
    MASTERSALT_NODETYPE="${MASTERSALT_NODETYPE:-"$SALT_NODETYPE"}"
    SALT_MASTER_CONTROLLER_DEFAULT="salt_master"
    SALT_MASTER_CONTROLLER_INPUTED="${SALT_MASTER_CONTROLLER}"
    SALT_MASTER_CONTROLLER="${SALT_MASTER_CONTROLLER:-$SALT_MASTER_CONTROLLER_DEFAULT}"
    SALT_MINION_CONTROLLER_DEFAULT="salt_minion"
    SALT_MINION_CONTROLLER_INPUTED="${SALT_MINION_CONTROLLER}"
    SALT_MINION_CONTROLLER="${SALT_MINION_CONTROLLER:-$SALT_MINION_CONTROLLER_DEFAULT}"

    # select the daemons to install but also
    # detect what is already present on the system
    case $SALT_CONTROLLER in
        salt_master)
            IS_SALT_MASTER="y";;
        *)
            IS_SALT_MINION="y";;
    esac
    case $MASTERSALT_CONTROLLER in
        mastersalt_master)
            IS_MASTERSALT_MASTER="y";;
        mastersalt_minion)
            IS_MASTERSALT_MINION="y";;
    esac
    if [[ -n "$MASTERSALT" ]];then
        IS_MASTERSALT_MINION="y"
    fi
    if [[ -e "${ETC_INIT}/salt-master.conf" ]]\
        || [[ -e "${ETC_INIT}.d/salt-master" ]]\
        || [[ -n "$IS_SALT_MASTER" ]];then
        IS_SALT="y"
        IS_SALT_MASTER="y"
        IS_SALT_MINION="y"
    fi
    if [[ -e "${ETC_INIT}/salt-minion.conf" ]]\
        || [[ -e "${ETC_INIT}.d/salt-minion" ]]\
        || [[ -n "$IS_SALT_MINION" ]];then
        IS_SALT="y"
        IS_SALT_MINION="y"
    fi

    if [[ -e "${ETC_INIT}/mastersalt-master.conf" ]]\
        || [[ -e "${ETC_INIT}.d/mastersalt-master" ]]\
        || [[ -n "$IS_MASTERSALT_MASTER" ]];then
        IS_MASTERSALT="y"
        IS_MASTERSALT_MASTER="y"
        IS_MASTERSALT_MINION="y"
    fi
    if [[ -e "${ETC_INIT}/mastersalt-minion.conf" ]]\
        || [[ -e "${ETC_INIT}.d/mastersalt-minion" ]]\
        || [[ -n "$IS_MASTERSALT_MINION" ]];then
        IS_MASTERSALT="y"
        IS_MASTERSALT_MINION="y"
    fi
    if [[ "$FORCE_IS_SALT" == "no" ]];then
        IS_SALT=""
        IS_SALT_MASTER=""
        IS_SALT_MINION=""
    fi
    if [[ "$FORCE_IS_MASTERSALT" == "no" ]];then
        IS_MASTERSALT=""
        IS_MASTERSALT_MASTER=""
        IS_MASTERSALT_MINION=""
    fi

    # force mode (via cmdline)
    if [[ "$FORCE_IS_MASTERSALT" == "no" ]];then IS_SALT_MINION="";fi
    if [[ "$FORCE_IS_SALT_MINION" == "no" ]];then IS_SALT_MINION="";fi
    if [[ "$FORCE_IS_SALT_MASTER" == "no" ]];then IS_SALT_MASTER="";fi
    if [[ "$FORCE_IS_MASTERSALT_MINION" == "no" ]];then IS_MASTERSALT_MINION="";fi
    if [[ "$FORCE_IS_MASTERSALT_MASTER" == "no" ]];then IS_MASTERSALT_MASTER="";fi
    if [[ -z "$IS_SALT_MINION" ]] && [[ -z "$IS_SALT_MASTER" ]];then
        IS_SALT=""
    fi
    if [[ -z "$IS_MASTERSALT_MINION" ]] && [[ -z "$IS_MASTERSALT_MASTER" ]];then
        IS_MASTERSALT=""
    fi

    # mastersalt variables
    if [[ -n "$IS_MASTERSALT" ]];then
        MASTERSALT_MASTER_CONTROLLER_DEFAULT="mastersalt_master"
        MASTERSALT_MASTER_CONTROLLER_INPUTED="${MASTERSALT_MASTER_CONTROLLER}"
        MASTERSALT_MASTER_CONTROLLER="${MASTERSALT_MASTER_CONTROLLER:-$MASTERSALT_MASTER_CONTROLLER_DEFAULT}"
        MASTERSALT_MINION_CONTROLLER_DEFAULT="mastersalt_minion"
        MASTERSALT_MINION_CONTROLLER_INPUTED="${MASTERSALT_MINION_CONTROLLER}"
        MASTERSALT_MINION_CONTROLLER="${MASTERSALT_MINION_CONTROLLER:-$MASTERSALT_MINION_CONTROLLER_DEFAULT}"
        MASTERSALT_INPUTED="${MASTERSALT}"
        # host running the mastersalt salt-master
        # - if we have not defined a mastersalt host,
        #    default to mastersalt.makina-corpus.net
        if [[ -n "$IS_MASTERSALT" ]];then
            if [[ -z "$MASTERSALT" ]];then
                MASTERSALT="$MASTERSALT_MAKINA_HOSTNAME"
            fi
            if [[ -e "$MASTERSALT_PILLAR/mastersalt.sls" ]];then
                MASTERSALT="$(grep "master: " $MASTERSALT_PILLAR/mastersalt.sls |awk '{print $2}'|tail -n 1)"
            fi
        fi

        MASTERSALT_MASTER_DNS="${MASTERSALT_MASTER_DNS:-${MASTERSALT}}"
        MASTERSALT_MASTER_IP="$(dns_resolve $MASTERSALT_MASTER_DNS)"
        MASTERSALT_MASTER_PORT="${MASTERSALT_MASTER_PORT:-"${MASTERSALT_PORT:-"4606"}"}"
        MASTERSALT_MASTER_PUBLISH_PORT="$(( ${MASTERSALT_MASTER_PORT} - 1 ))"

        MASTERSALT_MINION_DNS="${MASTERSALT_MINION_DNS:-"localhost"}"
        MASTERSALT_MINION_IP="$(dns_resolve $MASTERSALT_MINION_DNS)"

        if [[ "$MASTERSALT_MASTER_IP" == "127.0.0.1" ]];then
            MASTERSALT_MASTER_DNS="localhost"
        fi
        if [[ "$MASTERSALT_MINION_IP" == "127.0.0.1" ]];then
            MASTERSALT_MINION_DNS="localhost"
        fi

        if [[ -z "$MASTERSALT_MASTER_IP" ]];then
            die "MASTERSALT MASTER: invalid dns: $MASTERSALT_MASTER_DNS"
        fi
        if [[ -z "$MASTERSALT_MINION_IP" ]];then
            die "MASTERSALT MINION: invalid dns: $MASTERSALT_MINION_DNS"
        fi

        mastersalt_bootstrap_nodetype="${bootstrap_nodetypes_pref}.${MASTERSALT_NODETYPE}"
        mastersalt_bootstrap_master="${bootstrap_controllers_pref}.${MASTERSALT_MASTER_CONTROLLER}"
        mastersalt_bootstrap_minion="${bootstrap_controllers_pref}.${MASTERSALT_MINION_CONTROLLER}"
    fi

    # salt variables
    if [[ -n "$IS_SALT" ]];then
        SALT_MASTER_DNS="${SALT_MASTER_DNS:-"localhost"}"
        SALT_MASTER_IP="$(dns_resolve $SALT_MASTER_DNS)"
        SALT_MASTER_PORT="${SALT_MASTER_PORT:-"4506"}"
        SALT_MASTER_PUBLISH_PORT="$(( ${SALT_MASTER_PORT} - 1 ))"

        SALT_MINION_DNS="${SALT_MINION_DNS:-"localhost"}"
        SALT_MINION_IP="$(dns_resolve $SALT_MINION_DNS)"
        SALT_MINION_ID="${SALT_MINION_ID:-"$HOSTNAME"}"

        if [[ "$SALT_MASTER_IP" == "127.0.0.1" ]];then
            SALT_MASTER_DNS="localhost"
        fi
        if [[ "$SALT_MINION_IP" == "127.0.0.1" ]];then
            SALT_MINION_DNS="localhost"
        fi

        if [[ -z "$SALT_MASTER_IP" ]];then
            die "SALT MASTER: invalid dns: $SALT_MASTER_DNS"
        fi
        if [[ -z "$SALT_MINION_IP" ]];then
            die "SALT MINION: invalid dns: $SALT_MINION_DNS"
        fi

        bootstrap_nodetype="${bootstrap_nodetypes_pref}.${SALT_NODETYPE}"
        salt_bootstrap_master="${bootstrap_controllers_pref}.${SALT_MASTER_CONTROLLER}"
        salt_bootstrap_minion="${bootstrap_controllers_pref}.${SALT_MINION_CONTROLLER}"
    fi

    # --------- PROJECT VARS
    MAKINA_PROJECTS="makina-projects"
    PROJECTS_PATH="/srv/projects"
    PROJECT_URL="${PROJECT_URL:-""}"
    PROJECT_BRANCH="${PROJECT_BRANCH:-salt}"
    PROJECT_NAME="${PROJECT_NAME:-}"
    PROJECT_TOPSLS="${PROJECT_TOPSLS:-}"
    PROJECT_PATH="$PROJECTS_PATH/$PROJECT_NAME"
    PROJECTS_SALT_PATH="$SALT_ROOT/$MAKINA_PROJECTS"
    PROJECTS_PILLAR_PATH="$SALT_PILLAR/$MAKINA_PROJECTS"
    PROJECT_PILLAR_LINK="$PROJECTS_PILLAR_PATH/$PROJECT_NAME"
    PROJECT_PILLAR_PATH="$PROJECTS_PATH/$PROJECT_NAME/pillar"
    PROJECT_PILLAR_FILE="$PROJECT_PILLAR_PATH/init.sls"
    PROJECT_SALT_LINK="$SALT_ROOT/$MAKINA_PROJECTS/$PROJECT_NAME"
    PROJECT_SALT_PATH="$PROJECT_PATH/salt"
    PROJECT_TOPSLS_DEFAULT="$MAKINA_PROJECTS/$PROJECT_NAME/top.sls"
    PROJECT_TOPSTATE_DEFAULT="${MAKINA_PROJECTS}.${PROJECT_NAME}.top"
    PROJECT_PILLAR_STATE="${MAKINA_PROJECTS}.${PROJECT_NAME}"

    if [[ -n $PROJECT_URL ]] && [[ -z $PROJECT_NAME ]];then
        PROJECT_NAME="$(basename $(echo $PROJECT_URL|sed "s/.git$//"))"
    fi
    if [[ -n "$PROJECT_URL" ]] && [[ -z "$PROJECT_NAME" ]];then
        die "Please provide a \$PROJECT_NAME"
    fi

    # export variables to support a restart
    export IS_SALT IS_SALT_MASTER IS_SALT_MINION
    export IS_MASTERSALT IS_MASTERSALT_MASTER IS_MASTERSALT_MINION
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
    export MASTERSALT_NODETYPE SALT_NODETYPE
    export MASTERSALT_MINION_CONTROLLER MASTERSALT_MASTER_CONTROLLER
    export SALT_MINION_CONTROLLER SALT_MASTER_CONTROLLER
    #
    export SALT_MASTER_IP SALT_MASTER_DNS
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
}

# --------- PROGRAM START

recap_(){
    need_confirm="${1}"
    debug="${2:-$SALT_BOOT_DEBUG}"
    bs_yellow_log "--------------------------------------------------"
    bs_yellow_log " MAKINA-STATES BOOTSTRAPPER FOR $SALT_BOOT_OS"
    bs_yellow_log "   - $0"
    bs_yellow_log " Those informations have been written to:"
    bs_yellow_log "   - $TMPDIR/boot_salt_top"
    bs_yellow_log "--------------------------------------------------"
    bs_yellow_log "HOST variables:"
    bs_yellow_log "---------------"
    bs_log "HOSTNAME: $HOSTNAME"
    bs_log "DATE: $CHRONO"
    if [[ -n "$debug" ]];then
        bs_log "ROOT: $ROOT"
        bs_log "PREFIX: $PREFIX"
    fi
    if [[ -n "$IS_SALT" ]];then
        bs_yellow_log "---------------"
        bs_yellow_log "SALT variables:"
        bs_yellow_log "---------------"
        bs_log "SALT ROOT | PILLAR: $SALT_ROOT | $SALT_PILLAR"
        bs_log "SALT_NODETYPE: $SALT_NODETYPE"
        if [[ -n "$IS_SALT_MASTER" ]];then
            bs_log "SALT_MASTER_IP: $SALT_MASTER_IP"
        fi
        if [[ -n "$IS_SALT_MINION" ]];then
            bs_log "SALT_MASTER_DNS: $SALT_MASTER_DNS"
            bs_log "SALT_MASTER_PORT: $SALT_MASTER_PORT"
            bs_log "SALT_MINION_IP: $SALT_MINION_IP"
        fi
        if [[ -n "$debug" ]];then
            bs_log "SALT_MASTER_PUBLISH_PORT: $SALT_MASTER_PUBLISH_PORT"
            bs_log "bootstrap_nodetype: $bootstrap_nodetype"
            if [[ -n "$IS_SALT_MASTER" ]];then
                bs_log "salt_bootstrap_master: $salt_bootstrap_master"
                bs_log "SALT_MASTER_CONTROLLER: $SALT_MASTER_CONTROLLER"
                debug_msg "SALT_MASTER_CONTROLLER_INPUTED: $SALT_MASTER_CONTROLLER_INPUTED"
            fi
            if [[ -n "$IS_SALT_MINION" ]];then
                bs_log "salt_bootstrap_minion: $salt_bootstrap_minion"
                bs_log "SALT_MINION_CONTROLLER: $SALT_MINION_CONTROLLER"
                debug_msg "SALT_MINION_CONTROLLER_INPUTED: $SALT_MINION_CONTROLLER_INPUTED"
            fi
        fi
    fi
    if [[  -n "$IS_MASTERSALT" ]];then
        bs_yellow_log "---------------------"
        bs_yellow_log "MASTERSALT variables:"
        bs_yellow_log "---------------------"
        bs_log "MASTERSALT ROOT | PILLAR: $MASTERSALT_ROOT | $MASTERSALT_PILLAR"
        bs_log "MASTERSALT_NODETYPE: $MASTERSALT_NODETYPE"
        bs_log "MASTERSALT: $MASTERSALT"
        if [[ -n "$IS_MASTERSALT_MASTER" ]];then
            bs_log "MASTERSALT_MASTER_IP: $MASTERSALT_MASTER_IP"
            bs_log "MASTERSALT_MASTER_PUBLISH_PORT $MASTERSALT_MASTER_PUBLISH_PORT"
        fi
        if [[ -n "$IS_MASTERSALT_MINION" ]];then
            bs_log "MASTERSALT_MASTER_PORT: $MASTERSALT_MASTER_PORT"
            bs_log "MASTERSALT_MINION_IP: $MASTERSALT_MINION_IP"
            debug_msg "MASTERSALT_INPUTED: $MASTERSALT_INPUTED"
        fi
        if [[ -n "$debug" ]];then
            bs_log "mastersalt_bootstrap_nodetype: $mastersalt_bootstrap_nodetype"
            if [[ -n "$IS_MASTERSALT_MASTER" ]];then
                bs_log "mastersalt_bootstrap_master: $mastersalt_bootstrap_master"
                bs_log "MASTERSALT_MASTER_CONTROLLER: $MASTERSALT_MASTER_CONTROLLER"
                debug_msg "MASTERSALT_MASTER_CONTROLLER_INPUTED: $MASTERSALT_MASTER_CONTROLLER_INPUTED"
            fi
            if [[ -n "$IS_MASTERSALT_MINION" ]];then
                bs_log "mastersalt_bootstrap_minion: $mastersalt_bootstrap_minion"
                bs_log "MASTERSALT_MINION_CONTROLLER: $MASTERSALT_MINION_CONTROLLER"
                debug_msg "MASTERSALT_MINION_CONTROLLER_INPUTED: $MASTERSALT_MINION_CONTROLLER_INPUTED"
            fi
        fi
    fi
    if [[ -n "$PROJECT_URL" ]];then
        bs_yellow_log "--------------------"
        bs_yellow_log "PROJECT variables:"
        bs_yellow_log "--------------------"
        bs_log "PROJECT_URL:  ${PROJECT_URL}"
        bs_log "PROJECT_BRANCH: ${PROJECT_BRANCH}"
        bs_log "PROJECT_NAME: ${PROJECT_NAME}"
    fi
    bs_yellow_log "---------------------------------------------------"
    if [[ "$need_confirm" != "no" ]] && [[ -z "$SALT_BOOT_NOCONFIRM" ]];then
        bs_yellow_log "To not have this confirmation message, do:"
        bs_yellow_log "    export SALT_BOOT_NOCONFIRM='1'"
        interactive_tempo 60
    fi
}

recap() {
    recap_
    recap_ "no" "y" > "$TMPDIR/boot_salt_top"
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
        if [[ $ret != "0" ]];then
            die $ret "Install of zmq3 failed"
        fi
        ret="$?"
        teardown_backports && apt-get update
        if [[ $ret != "0" ]];then
            die $ret "Teardown backports failed"
        fi
    fi
    for i in $BASE_PACKAGES;do
        if [[ $(dpkg-query -s $i 2>/dev/null|egrep "^Status:"|grep installed|wc -l)  == "0" ]];then
            to_install="$to_install $i"
        fi
    done
    if [[ -n "$to_install" ]];then
        bs_log "Installing pre requisites: $to_install"
        echo 'changed=yes comment="prerequisites installed"'
        apt-get update && lazy_apt_get_install $to_install
    fi
}

# check if salt got errors:
# - First, check for fatal errors (retcode not in [0, 2]
# - in case of executions:
# - We will check for fatal errors in logs
# - We will check for any false return in output state structure
get_saltcall_args() {
    get_module_args "$SALT_ROOT" "${SALT_MS}"
}

get_mastersaltcall_args() {
    get_module_args "$MASTERSALT_ROOT" "$MASTERSALT_MS"
}

salt_call_wrapper_() {
    last_salt_retcode=-1
    salt_call_prefix=$1;shift
    outf="$SALT_BOOT_OUTFILE"
    logf="$SALT_BOOT_LOGFILE"
    cmdf="$SALT_BOOT_CMDFILE"
    saltargs=" --retcode-passthrough --out=yaml --out-file="$outf" --log-file="$logf""
    if [[ -n $SALT_BOOT_DEBUG ]];then
        saltargs="$saltargs -l${SALT_BOOT_DEBUG_LEVEL}"
    else
        saltargs="$saltargs -lquiet"
    fi
    $salt_call_prefix/bin/salt-call $saltargs $@
    echo "$(date): $salt_call_prefix/bin/salt-call $saltargs $@" >> "$cmdf"
    last_salt_retcode=$?
    STATUS="NOTSET"
    if [[ "$last_salt_retcode" != "0" ]] && [[ "$last_salt_retcode" != "2" ]];then
        STATUS="ERROR"
        bs_log "salt-call ERROR, check $logf and $outf for details" 2>&2
        last_salt_retcode=100
    fi
    no_output_log=""
    if [[ -e "$logf" ]];then
        if grep  -q "No matching sls found" "$logf";then
            STATUS="ERROR"
            bs_log "salt-call  ERROR DETECTED : No matching sls found" 1>&2
            last_salt_retcode=101
            no_output_log="y"
        elif egrep -q "\[salt.(state|crypt)       \]\[ERROR   \]" "$logf";then
            STATUS="ERROR"
            bs_log "salt-call  ERROR DETECTED, check $logf for details" 1>&2
            egrep "\[salt.state       \]\[ERROR   \]" "$logf" 1>&2;
            last_salt_retcode=102
            no_output_log="y"
        elif egrep  -q "Rendering SLS .*failed" "$logf";then
            STATUS="ERROR"
            bs_log "salt-call  ERROR DETECTED : Rendering failed" 1>&2
            last_salt_retcode=103
            no_output_log="y"
        fi
    fi
    if [[ -e "$outf" ]];then
        if egrep -q "result: false" "$outf";then
            if [[ -z "$no_output_log" ]];then
                bs_log "partial content of $outf, check this file for full output" 1>&2
            fi
            egrep -B4 "result: false" "$outf" 1>&2;
            last_salt_retcode=104
            STATUS="ERROR"
        elif egrep  -q "Rendering SLS .*failed" "$outf";then
            if [[ -z "$no_output_log" ]];then
                bs_log "salt-call  ERROR DETECTED : Rendering failed (o)" 1>&2
            fi
            last_salt_retcode=103
            STATUS="ERROR"
        fi
    fi
    if [[ "$STATUS" != "ERROR" ]] \
        && [[ "$last_salt_retcode" != "0" ]]\
        && [[ "$last_salt_retcode" != "2" ]];\
    then
        last_salt_retcode=0
    fi
    for i in "$SALT_BOOT_OUTFILE" "$SALT_BOOT_LOGFILE" "$SALT_BOOT_CMDFILE";do
        if [[ -e "$i" ]];then
            chmod 600 "$i" &> /dev/null
        fi
    done
}

salt_call_wrapper() {
    chrono="$(get_chrono)"
    if [[ ! -d $BOOT_LOGS ]];then
        mkdir -pv $BOOT_LOGS
    fi
    SALT_BOOT_OUTFILE="$BOOT_LOGS/boot_salt.${chrono}.out"
    SALT_BOOT_LOGFILE="$BOOT_LOGS/boot_salt.${chrono}.log"
    SALT_BOOT_CMDFILE="$BOOT_LOGS/boot_salt_cmd"
    salt_call_wrapper_ ${SALT_MS} $(get_saltcall_args) $@
}

mastersalt_call_wrapper() {
    chrono="$(get_chrono)"
    if [[ ! -d $MBOOT_LOGS ]];then
        mkdir -pv $MBOOT_LOGS
    fi
    SALT_BOOT_OUTFILE="$MBOOT_LOGS/boot_salt.${chrono}.out"
    SALT_BOOT_LOGFILE="$MBOOT_LOGS/boot_salt.${chrono}.log"
    SALT_BOOT_CMDFILE="$MBOOT_LOGS/boot_salt_cmd"
    salt_call_wrapper_ $MASTERSALT_MS $(get_mastersaltcall_args) -c $MCONF_PREFIX $@
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
        bs_log "Grain '$grain' already set"
    fi
}

check_restartmarker_and_maybe_restart() {
    if [[ -z $SALT_BOOT_IN_RESTART ]];then
        if [[ -n "$SALT_BOOT_NEEDS_RESTART" ]];then
            touch "${SALT_MS}/.bootsalt_need_restart"
        fi
        if [[ -e "${SALT_MS}/.bootsalt_need_restart" ]] && [[ -z "$SALT_BOOT_NO_RESTART" ]];then
            chmod +x "${SALT_MS}/_scripts/boot-salt.sh"
            export SALT_BOOT_NO_RESTART="1"
            export SALT_BOOT_IN_RESTART="1"
            export SALT_BOOT_NOCONFIRM='1'
            mbootsalt="$MASTERSALT_MS/_scripts/boot-salt.sh"
            bootsalt="${SALT_MS}/_scripts/boot-salt.sh"
            if [[ "$LAUNCHER" == "$mbootsalt" ]];then
                bootsalt="$mbootsalt"
            fi
            bs_log "Restarting $bootsalt which needs to update itself"
            "$bootsalt" $LAUNCH_ARGS && rm -f "${SALT_MS}/.bootsalt_need_restart"
            exit $?
        fi
    fi
}

setup_and_maybe_update_code() {
    bs_log "Create base directories"
    if [[ -n "$IS_SALT" ]];then
        for i in "$SALT_PILLAR" "$SALT_ROOT";do
            if [[ ! -d "$i" ]];then
                mkdir -pv "$i"
            fi
        done
    fi
    if [[  -n "$IS_MASTERSALT" ]];then
        for i in "$MASTERSALT_PILLAR" "$MASTERSALT_ROOT";do
            if [[ ! -d "$i" ]];then
                mkdir -pv "$i"
            fi
        done
    fi
    SALT_MSS=""
    if [[ -n "$IS_SALT" ]];then
        SALT_MSS="${SALT_MSS} $SALT_MS"
    fi
    if [[  -n "$IS_MASTERSALT" ]];then
        SALT_MSS="${SALT_MSS} $MASTERSALT_MS"
    fi
    is_offline="$(test_online)"
    minion_keys="$(find $CONF_PREFIX/pki/master/{minions_pre,minions} -type f 2>/dev/null|wc -l)"
    if [[ "$is_offline" != "0" ]];then
        if [[ ! -e $CONF_PREFIX ]]\
            || [[ "$minion_keys" == "0" ]]\
            || [[ ! -e "${SALT_MS}/src/salt" ]]\
            || [[ ! -e "${SALT_MS}/bin/salt-call" ]]\
            || [[ ! -e "${SALT_MS}/bin/salt" ]];then
            bs_log "Offline mode and installation not enougthly completed, bailing out"
            exit -1
        fi
    fi
    if [[ "$is_offline" == "0" ]]\
        && [[ -z "$SALT_BOOT_IN_RESTART" ]]\
        && [[ -z "$SALT_BOOT_SKIP_CHECKOUTS" ]];then
        i_prereq || die_in_error " [bs] Failed install rerequisites"
        if [[ -z "$SALT_BOOT_SKIP_CHECKOUTS" ]];then
            bs_yellow_log "If you want to skip checkouts, next time do export SALT_BOOT_SKIP_CHECKOUTS=1"
        fi
        for ms in ${SALT_MSS};do
            if [[ ! -d "$ms/.git" ]];then
                git clone "$STATES_URL" "$ms"
                SALT_BOOT_NEEDS_RESTART="1"
                if [[ "$?" == "0" ]];then
                    die_in_error " [bs] Downloaded makina-states ($ms)"
                else
                    die_in_error " [bs] Failed to download makina-states ($ms)"
                fi
            fi
            #chmod +x ${SALT_MS}/_scripts/install_salt_modules.sh
            #"${SALT_MS}/_scripts/install_salt_modules.sh" "$SALT_ROOT"
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
                    git fetch --tags origin &> /dev/null
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
        for i in ${ROOT} ${ROOT}usr ${ROOT}usr/local;do
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
    cleanup_previous_venv ${SALT_MS}
    cleanup_previous_venv /srv/salt-venv
    cd ${SALT_MS}
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
        || [[ ! -e "$ms/bin/salt-call" ]]\
        || [[ ! -e "$ms/bin/salt-key" ]]\
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
    if [[  -n "$IS_SALT" ]];then
        run_ms_buildout ${SALT_MS}
    fi
    if [[  -n "$IS_MASTERSALT" ]];then
        if [[ ! -e $MASTERSALT_ROOT/makina-states/.installed.cfg ]];then
            bs_log "Copying base tree, this can take a while"
            # -a without time
            rsync -rlpgoD ${SALT_MS}/ $MASTERSALT_ROOT/makina-states/ --exclude=*pyc --exclude=*pyo --exclude=.installed.cfg --exclude=.mr.developer.cfg --exclude=.bootlogs
            cd $MASTERSALT_ROOT/makina-states
            rm -rf .installed.cfg .mr.developer.cfg parts
        fi
        run_ms_buildout $MASTERSALT_ROOT/makina-states/
    fi
}

create_salt_skeleton(){
    # create etc directory
    if [[ ! -e $CONF_PREFIX ]];then mkdir $CONF_PREFIX;fi
    if [[ ! -e $CONF_PREFIX/master.d ]];then mkdir $CONF_PREFIX/master.d;fi
    if [[ ! -e $CONF_PREFIX/minion.d ]];then mkdir $CONF_PREFIX/minion.d;fi
    if [[ ! -e $CONF_PREFIX/master ]];then
        cat > $CONF_PREFIX/master << EOF
file_roots: {"base":["$SALT_ROOT"]}
pillar_roots: {"base":["$SALT_PILLAR"]}
EOF
    fi
    if [[ ! -e $CONF_PREFIX/minion ]];then
        cat > $CONF_PREFIX/minion << EOF
id: $SALT_MINION_ID
master: $SALT_MASTER_DNS
master_port: $SALT_MASTER_PORT
file_roots: {"base":["$SALT_ROOT"]}
pillar_roots: {"base":["$SALT_PILLAR"]}
module_dirs: [$SALT_ROOT/_modules, ${SALT_MS}/_modules]
returner_dirs: [$SALT_ROOT/_returners, ${SALT_MS}/_returners]
states_dirs: [$SALT_ROOT/_states, ${SALT_MS}/_states]
render_dirs: [$SALT_ROOT/_renderers, ${SALT_MS}/_renderers]
EOF
    fi

    # create etc/mastersalt
    if [[  -n "$IS_MASTERSALT" ]];then
        if [[ ! -e $MCONF_PREFIX ]];then mkdir $MCONF_PREFIX;fi
        if [[ ! -e $MCONF_PREFIX/master.d ]];then mkdir $MCONF_PREFIX/master.d;fi
        if [[ ! -e $MCONF_PREFIX/minion.d ]];then mkdir $MCONF_PREFIX/minion.d;fi
        if [[ ! -e $MCONF_PREFIX/master ]];then
            cat > $MCONF_PREFIX/master << EOF
file_roots: {"base":["$MASTERSALT_ROOT"]}
pillar_roots: {"base":["$MASTERSALT_PILLAR"]}
EOF
        fi
        if [[ ! -e $MCONF_PREFIX/minion ]];then
            cat > $MCONF_PREFIX/minion << EOF
id: $SALT_MINION_ID
master: $MASTERSALT_MASTER_DNS
master_port: $MASTERSALT_MASTER_PORT
file_roots: {"base":["$MASTERSALT_ROOT"]}
pillar_roots: {"base":["$MASTERSALT_PILLAR"]}
module_dirs: [$MASTERSALT_ROOT/_modules, $MASTERSALT_MS/_modules]
returner_dirs: [$MASTERSALT_ROOT/_returners, $MASTERSALT_MS/_returners]
states_dirs: [$MASTERSALT_ROOT/_states, $MASTERSALT_MS/_states]
render_dirs: [$MASTERSALT_ROOT/_renderers, $MASTERSALT_MS/_renderers]
EOF
        fi
    fi

    # create pillars
    PILLAR_ROOTS="$SALT_PILLAR"
    if [[  -n "$IS_MASTERSALT" ]];then
        PILLAR_ROOTS="$SALT_PILLAR_ROOTS $MASTERSALT_PILLAR"
    fi
    for pillar_root in $SALT_PILLAR_ROOTS;do
        # Create a default top.sls in the pillar if not present
        if [[ ! -f $pillar_root/top.sls ]];then
            debug_msg "creating default $pillar_root/top.sls"
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
    # Create a default top.sls in the tree if not present
    TOPS_FILES="$SALT_ROOT/top.sls"
    if [[ -n "$IS_MASTERSALT_MASTER" ]];then
        TOPS_FILES="$TOPS_FILES $MASTERSALT_ROOT/top.sls"
    fi
    for topf in $TOPS_FILES;do
        if [[ ! -f $topf ]];then
            debug_msg "creating default salt's $topf"
            cat > "$topf" << EOF
#
# This is the salt states configuration file, link here all your
# environment states files to their respective minions
#
base:
  '*':
EOF
        fi
        # add makina-state.top if not present
        if [[ "$(egrep -- "- makina-states\.top\s*$" $topf|wc -l)" == "0" ]];then
            debug_msg "Adding makina-states.top to $topf"
            sed -re "/('|\")\*('|\"):/ {
a\    - makina-states.top
}" -i $topf
        fi
    done
    if [[ "$(grep -- "- salt" $SALT_PILLAR/top.sls|wc -l)" == "0" ]];then
        debug_msg "Adding salt to default top salt pillar"
        sed -re "/('|\")\*('|\"):/ {
a\    - salt
}" -i "$SALT_PILLAR/top.sls"
    fi
    # Create a default salt.sls in the pillar if not present
    if [[ ! -e "$SALT_PILLAR/salt.sls" ]];then
        debug_msg "Creating default pillar's salt.sls"
        echo 'salt:' > "$SALT_PILLAR/salt.sls"
    fi
    if [[ "$(egrep -- "^salt:" "$SALT_PILLAR/salt.sls"|wc -l)" == "0" ]];then
        echo ''  >> "$SALT_PILLAR/salt.sls"
        echo 'salt:' >> "$SALT_PILLAR/salt.sls"
    fi
    if [[ "$(egrep -- "\s*minion:\s*$" "$SALT_PILLAR/salt.sls"|wc -l)" == "0" ]];then
        debug_msg "Adding minion info to pillar"
        sed -re "/^salt:\s*$/ {
a\  minion:
a\    id: ${SALT_MINION_ID}
a\    interface: $SALT_MINION_IP
a\    master: $SALT_MASTER_DNS
a\    master_port: $SALT_MASTER_PORT
}" -i "$SALT_PILLAR/salt.sls"
    fi
    # do no setup stuff for master for just a minion
    if [[ "$SALT_MASTER_DNS" == "localhost" ]] \
       && [[ "$(egrep -- "\s*master:\s*$" "$SALT_PILLAR/salt.sls"|wc -l)" == "0" ]];then
        debug_msg "Adding master info to pillar"
        sed -re "/^salt:\s*$/ {
a\  master:
a\    interface: $SALT_MASTER_IP
a\    publish_port: $SALT_MASTER_PUBLISH_PORT
a\    ret_port: $SALT_MASTER_PORT
}" -i "$SALT_PILLAR/salt.sls"
    fi
    # --------- MASTERSALT
    # Set default mastersalt  pillar
    if [[ -n "$IS_MASTERSALT" ]];then
        if [[ "$(grep -- "- mastersalt" "$MASTERSALT_PILLAR/top.sls"|wc -l)" == "0" ]];then
            debug_msg "Adding mastersalt info to top mastersalt pillar"
            sed -re "/('|\")\*('|\"):/ {
a\    - mastersalt
}" -i "$MASTERSALT_PILLAR/top.sls"
        fi
        if [[ ! -f "$MASTERSALT_PILLAR/mastersalt.sls" ]];then
            debug_msg "Creating mastersalt configuration file"
            echo "mastersalt:" >  "$MASTERSALT_PILLAR/mastersalt.sls"
        fi
        if [[ "$(egrep -- "^mastersalt:\s*$" "$MASTERSALT_PILLAR/mastersalt.sls"|wc -l)" == "0" ]];then
            echo ''  >> "$MASTERSALT_PILLAR/mastersalt.sls"
            echo 'mastersalt:' >> "$MASTERSALT_PILLAR/mastersalt.sls"
        fi
        if [[ "$(egrep -- "^\s*minion:" "$MASTERSALT_PILLAR/mastersalt.sls"|wc -l)" == "0" ]];then
            debug_msg "Adding mastersalt minion info to mastersalt pillar"
            sed -re "/^mastersalt:\s*$/ {
a\  minion:
a\    id: ${SALT_MINION_ID}
a\    interface: ${MASTERSALT_MINION_IP}
a\    master: ${MASTERSALT_MASTER_DNS}
a\    master_port: ${MASTERSALT_MASTER_PORT}
}" -i "$MASTERSALT_PILLAR/mastersalt.sls"
        fi
        if [[ -n "$IS_MASTERSALT_MASTER" ]];then
            if [[ "$(egrep -- "\s+master:\s*$" "$MASTERSALT_PILLAR/mastersalt.sls"|wc -l)" == "0" ]];then
                debug_msg "Adding mastersalt master info to mastersalt pillar"
                sed -re "/^mastersalt:\s*$/ {
a\  master:
a\    interface: $MASTERSALT_MASTER_IP
a\    ret_port: ${MASTERSALT_MASTER_PORT}
a\    publish_port: ${MASTERSALT_MASTER_PUBLISH_PORT}
}" -i "$MASTERSALT_PILLAR/mastersalt.sls"
            fi
        fi
    fi
}

# ------------ SALT INSTALLATION PROCESS

get_minion_id() {
    cat $CONF_PREFIX/minion_id 2> /dev/null
}

lazy_start_salt_daemons() {
    if [[ -n "$IS_SALT_MASTER" ]];then
        master_processes="$($PS aux|grep salt-master|grep -v mastersalt|grep -v grep|wc -l)"
        if [[ "$master_processes" == "0" ]];then
            restart_local_masters
            sleep 2
        fi
        master_processes="$($PS aux|grep salt-master|grep -v mastersalt|grep -v grep|wc -l)"
        if [[ "$master_processes" == "0" ]];then
            die_in_error "Salt Master start failed"
        fi
    fi
    if [[ -n "$IS_SALT_MINION" ]];then
        minion_processes="$($PS aux|grep salt-minion|grep -v mastersalt|grep -v grep|wc -l)"
        if [[ "$minion_processes" == "0" ]];then
            restart_local_minions
            sleep 2
            minion_processes="$($PS aux|grep salt-minion|grep -v mastersalt|grep -v grep|wc -l)"
            if [[ "$master_processes" == "0" ]];then
                die_in_error "Salt Minion start failed"
            fi
        fi
    fi

}

install_salt_daemons() {
    # --------- check if we need to run salt setup's
    RUN_SALT_BOOTSTRAP=""
    if [[ "$SALT_MASTER_DNS" == "localhost" ]];then
        if  [[ ! -e "$CONF_PREFIX/pki/master/master.pem" ]]\
            || [[ ! -e "$CONF_PREFIX/master.d/00_global.conf" ]];then
            RUN_MASTERSALT_BOOTSTRAP="1"
        fi
    fi
    if     [[ ! -e "$CONF_PREFIX" ]]\
        || [[ ! -e "$CONF_PREFIX/minion.d/00_global.conf" ]]\
        || [[ -e "${SALT_MS}/.reboostrap" ]]\
        || [[ "$(grep makina-states.controllers.salt_ "$CONF_PREFIX/grains" |wc -l)" == "0" ]]\
        || [[ ! -e "$CONF_PREFIX/pki/minion/minion.pem" ]]\
        || [[ ! -e "$BIN_DIR/salt" ]]\
        || [[ ! -e "$BIN_DIR/salt-call" ]]\
        || [[ ! -e "$BIN_DIR/salt-cp" ]]\
        || [[ ! -e "$BIN_DIR/salt-key" ]]\
        || [[ ! -e "$BIN_DIR/salt-master" ]]\
        || [[ ! -e "$BIN_DIR/salt-minion" ]]\
        || [[ ! -e "$BIN_DIR/salt-ssh" ]]\
        || [[ ! -e "$BIN_DIR/salt-syndic" ]]\
        || [[ ! -e "$CONF_PREFIX/pki/minion/minion.pem" ]];then
        if [[ -e "${SALT_MS}/.reboostrap" ]];then
            rm -f "${SALT_MS}/.rebootstrap"
        fi
        RUN_SALT_BOOTSTRAP="1"
    fi

    # --------- SALT install
    if [[ -n "$RUN_SALT_BOOTSTRAP" ]];then
        ds=y
        # kill salt running daemons if any
        if [[ "$SALT_MASTER_DNS" == "localhost" ]];then
            killall_local_masters
        fi
        if [[ -n "$IS_SALT_MINION" ]];then
            killall_local_minions
        fi

        bs_log "Boostrapping salt"

        # run salt master+minion boot_nodetype bootstrap
        bs_log "Running salt nodetype bootstrap: $bootstrap_nodetype"
        salt_call_wrapper --local state.sls $bootstrap_nodetype
        if [[ -n "$SALT_BOOT_DEBUG" ]];then cat $SALT_BOOT_OUTFILE;fi
        warn_log
        if [[ "$last_salt_retcode" != "0" ]];then
            bs_log "Failed bootstrap nodetype: $bootstrap_nodetype"
            exit -1
        fi

        # run mastersalt master+minion boot_nodetype bootstrap
        run_salt_bootstrap $salt_bootstrap_nodetype

        # run mastersalt master setup
        if [[ -n "$IS_MASTERSALT_MASTER" ]];then
            run_salt_bootstrap $salt_bootstrap_master
        fi

        # run mastersalt minion setup
        if [[ -n "$IS_SALT_MINION" ]];then
            run_salt_bootstrap $salt_bootstrap_minion
        fi

        # restart salt daemons
        if [[ -n "$IS_SALT_MASTER" ]];then
            # restart salt salt-master after setup
            bs_log "Forcing salt master restart"
            restart_local_masters
            sleep 10
        fi
        # restart salt minion
        if [[ -n "$IS_SALT_MINION" ]];then
            bs_log "Forcing salt minion restart"
            restart_local_minions
        fi
        SALT_BOOT_NOW_INSTALLED="y"
    else
        bs_log "Skip salt installation, already done"
    fi
    lazy_start_salt_daemons
}

killall_local_mastersalt_masters() {
    $PS aux|egrep "salt-(master|syndic)"|grep mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
}

killall_local_mastersalt_minions() {
    $PS aux|egrep "salt-(minion)"|grep mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
}

killall_local_masters() {
    $PS aux|egrep "salt-(master|syndic)"|grep -v mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
}

killall_local_minions() {
    $PS aux|egrep "salt-(minion)"|grep -v mastersalt|awk '{print $2}'|xargs kill -9 &> /dev/null
}

restart_local_mastersalt_masters() {
    killall_local_mastersalt_masters
    service mastersalt-master restart
}

restart_local_mastersalt_minions() {
    killall_local_mastersalt_minions
    service mastersalt-minion restart
}

restart_local_masters() {
    killall_local_masters
    service salt-master restart
}

restart_local_minions() {
    killall_local_minions
    service salt-minion restart
}

salt_ping_test() {
    salt_call_wrapper test.ping &> /dev/null
    echo $last_salt_retcode
}

mastersalt_ping_test() {
    mastersalt_call_wrapper test.ping &> /dev/null
    echo $last_salt_retcode
}

minion_challenge() {
    if [[ -z "$IS_SALT_MINION" ]];then return;fi
    challenged_ms=""
    global_tries="60"
    inner_tries="10"
    for i in `seq $global_tries`;do
        restart_local_minions
        resultping="1"
        for j in `seq $inner_tries`;do
            resultping="$(salt_ping_test)"
            if [[ "$resultping" != "0" ]];then
                bs_yellow_log " sub challenge try ($i/$global_tries) ($j/$inner_tries)"
                sleep 1
            else
                break
            fi
        done
        if [[ "$resultping" != "0" ]];then
            bs_log "Failed challenge salt keys on master, retry $i/$global_tries"
            challenged_ms=""
        else
            challenged_ms="y"
            bs_log "Successfull challenge salt keys on master"
            break
        fi
    done
}

mastersalt_minion_challenge() {
    if [[ -z "$IS_MASTERSALT_MINION" ]];then return;fi
    challenged_ms=""
    global_tries="60"
    inner_tries="10"
    for i in `seq $global_tries`;do
        restart_local_minions
        resultping="1"
        for j in `seq $inner_tries`;do
            resultping="$(mastersalt_ping_test)"
            if [[ "$resultping" != "0" ]];then
                bs_yellow_log " sub challenge try ($i/$global_tries) ($j/$inner_tries)"
                sleep 1
            else
                break
            fi
        done
        if [[ "$resultping" != "0" ]];then
            bs_log "Failed challenge mastersalt keys on $MASTERSALT, retry $i/$global_tries"
            challenged_ms=""
        else
            challenged_ms="y"
            bs_log "Successfull challenge mastersalt keys on $MASTERSALT"
            break
        fi
    done
}

salt_master_connectivity_check() {
    if [[ $(check_connectivity $SALT_MASTER_IP $SALT_MASTER_PORT) != "0" ]];then
        die_in_error "SaltMaster is unreachable ($SALT_MASTER_IP/$SALT_MASTER_PORT)"
    fi
}

mastersalt_master_connectivity_check() {
    if [[ $(check_connectivity $MASTERSALT $MASTERSALT_MASTER_PORT) != "0" ]];then
        die_in_error "MastersaltMaster is unreachable ($MASTERSALT/$MASTERSALT_MASTER_PORT)"
    fi
}

challenge_message() {
    minion_id="$(get_minion_id)"
    bs_log "****************************************************************"
    bs_log "     GO ACCEPT THE KEY ON SALT_MASTER  ($SALT_MASTER_IP) !!! "
    bs_log "     You need on this box to run salt-key -y -a $minion_id"
    bs_log "****************************************************************"
}

make_association() {
    if [[ -z $IS_SALT_MINION ]];then return;fi
    minion_keys="$(find $CONF_PREFIX/pki/master/minions -type f 2>/dev/null|wc -l)"
    minion_id="$(get_minion_id)"
    registered=""
    debug_msg "Entering association routine"
    bs_log "If the bootstrap program seems to block here"
    challenge_message
    debug_msg "ack"
    if [[ -z "$minion_id" ]];then
        bs_yellow_log "Minion did not start correctly, the minion_id cache file is empty, trying to restart"
        restart_local_minions
        sleep 3
        minion_id="$(get_minion_id)"
        if [[ -z "$minion_id" ]];then
            die_in_error "Minion did not start correctly, the minion_id cache file is always empty"
        fi
    fi
    # only accept key on fresh install (no keys stored)
    if [[ "$(salt_ping_test)" == "0" ]];\
    then
        debug_msg "Salt minion \"$minion_id\" already registered on master"
        minion_id="$(get_minion_id)"
        registered="1"
        echo "changed=false comment='salt minion already registered'"
    else
        if [[ "$SALT_MASTER_DNS" == "localhost" ]];then
            debug_msg "Forcing salt master restart"
            restart_local_masters
            sleep 10
        fi
        if [[ "$SALT_MASTER_DNS" != "localhost" ]] &&  [[ -z "$SALT_NO_CHALLENGE" ]];then
            challenge_message
            bs_log " We are going to wait 10 minutes for you to setup the minion on mastersalt and"
            bs_log " setup an entry for this specific minion"
            bs_log " export SALT_NO_CHALLENGE=1 to remove the temporisation (enter to continue when done)"
            interactive_tempo $((10 * 60))
        else
            bs_log "  [*] No temporisation for challenge, trying to spawn the minion"
            if [[ "$SALT_MASTER_DNS" == "localhost" ]];then
                salt-key -y -a "$minion_id"
                ret="$?"
                if [[ "$ret" != "0" ]];then
                    bs_log "Failed accepting keys"
                    warn_log
                    exit -1
                else
                    bs_log "Accepted key"
                fi
            fi
        fi
        debug_msg "Forcing salt minion restart"
        restart_local_minions
        salt_master_connectivity_check
        bs_log "Waiting for salt minion key hand-shake"
        minion_id="$(get_minion_id)"
        if [[ "$(salt_ping_test)" == "0" ]] && [[ "$minion_keys" != "0" ]];then
            # sleep 15 seconds giving time for the minion to wake up
            bs_log "Salt minion \"$minion_id\" registered on master"
            registered="1"
            echo "changed=yes comment='salt minion already registered'"
        else
            minion_challenge
            if [[ -z "$challenged_ms" ]];then
                bs_log "Failed accepting salt key on master for $minion_id"
                warn_log
                exit -1
            fi
            minion_id="$(get_minion_id)"
            registered="1"
            echo "changed=yes comment='salt minion already registered'"
        fi
        if [[ -z "$registered" ]];then
            bs_log "Failed accepting salt key on $SALT_MASTER_IP for $minion_id"
            warn_log
            exit -1
        fi
    fi
}

challenge_mastersalt_message() {
    minion_id="$(get_minion_id)"
    bs_log "****************************************************************"
    bs_log "    GO ACCEPT THE KEY ON MASTERSALT ($MASTERSALT) !!! "
    bs_log "    You need on this box to run mastersalt-key -y -a $minion_id"
    bs_log "****************************************************************"
}

make_mastersalt_association() {
    if [[ -z $IS_MASTERSALT_MINION ]];then return;fi
    minion_id="$(cat $CONF_PREFIX/minion_id &> /dev/null)"
    registered=""
    debug_msg "Entering mastersalt association routine"
    bs_log "If the bootstrap program seems to block here"
    challenge_mastersalt_message
    debug_msg "ack"
    if [[ -z "$minion_id" ]];then
        bs_yellow_log "Minion did not start correctly, the minion_id cache file is empty, trying to restart"
        restart_local_mastersalt_minions
        sleep 3
        minion_id="$(get_minion_id)"
        if [[ -z "$minion_id" ]];then
            die_in_error "Minion did not start correctly, the minion_id cache file is always empty"
        fi
    fi
    if [[ "$(mastersalt_ping_test)" == "0" ]];then
        debug_msg "Mastersalt minion \"$minion_id\" already registered on $MASTERSALT"
        echo "changed=false comment='mastersalt minion already registered'"
    else
        if [[ "$MASTERSALT_MASTER_IP" == "127.0.0.0.1" ]];then
            debug_msg "Forcing mastersalt master restart"
            restart_local_mastersalt_masters
        fi
        if [[ "$MASTERSALT_MASTER_DNS" != "localhost" ]] && [[ -z "$MASTERSALT_NO_CHALLENGE" ]];then
            challenge_mastersalt_message
            bs_log " We are going to wait 10 minutes for you to setup the minion on mastersalt and"
            bs_log " setup an entry for this specific minion"
            bs_log " export MASTERSALT_NO_CHALLENGE=1 to remove the temporisation (enter to continue when done)"
            interactive_tempo $((10*60))
        else
            bs_log "  [*] No temporisation for challenge, trying to spawn the mastersalt minion"
            # in case of a local mastersalt, auto accept the minion key
            if [[ "$MASTERSALT_MASTER_DNS" == "localhost" ]];then
                mastersalt-key -y -a "$minion_id"
                ret="$?"
                if [[ "$ret" != "0" ]];then
                    bs_log "Failed accepting mastersalt keys"
                    warn_log
                    exit -1
                else
                    bs_log "Accepted mastersalt key"
                fi
            fi
        fi
        debug_msg "Forcing mastersalt minion restart"
        restart_local_mastersalt_minions
        mastersalt_master_connectivity_check
        bs_log "Waiting for mastersalt minion key hand-shake"
        minion_id="$(get_minion_id)"
        if [[ "$(salt_ping_test)" == "0" ]];then
            echo "changed=yes comment='mastersalt minion registered'"
            bs_log "Salt minion \"$minion_id\" registered on master"
            registered="1"
            echo "changed=yes comment='salt minion registered'"
        else
            mastersalt_minion_challenge
            if [[ -z "$challenged_ms" ]];then
                bs_log "Failed accepting salt key on master for $minion_id"
                warn_log
                exit -1
            fi
            minion_id="$(get_minion_id)"
            registered="1"
            echo "changed=yes comment='salt minion registered'"
        fi
        if [[ -z "$registered" ]];then
            bs_log "Failed accepting mastersalt key on $MASTERSALT for $minion_id"
            warn_log
            exit -1
        fi
    fi
}

lazy_start_mastersalt_daemons() {
    if [[ -n "$IS_MASTERSALT_MASTER" ]];then
        master_processes="$($PS aux|grep salt-master|grep mastersalt|grep -v grep|wc -l)"
        if [[ "$master_processes" == "0" ]];then
            restart_local_mastersalt_masters
            sleep 2
        fi
        master_processes="$($PS aux|grep salt-master|grep mastersalt|grep -v grep|wc -l)"
        if [[ "$master_processes" == "0" ]];then
            die_in_error "Masteralt Master start failed"
        fi
    fi
    if [[ -n "$IS_MASTERSALT_MINION" ]];then
        minion_processes="$($PS aux|grep salt-minion|grep mastersalt|grep -v grep|wc -l)"
        if [[ "$minion_processes" == "0" ]];then
            restart_local_mastersalt_minions
            sleep 2
            minion_processes="$($PS aux|grep salt-minion|grep mastersalt|grep -v grep|wc -l)"
            if [[ "$master_processes" == "0" ]];then
                die_in_error "Masteralt Minion start failed"
            fi
        fi
    fi

}

run_salt_bootstrap_() {
    salt_type=$1
    bs=$2
    bs_log "Running ${salt_type} bootstrap: $bs"
    ${salt_type}_call_wrapper --local state.sls $bs
    if [[ -n "$SALT_BOOT_DEBUG" ]];then cat $SALT_BOOT_OUTFILE;fi
    warn_log
    if [[ "$last_salt_retcode" != "0" ]];then
        echo "$salt_type: Failed bootstrap: $bs"
        exit -1
    fi
}

run_salt_bootstrap() {
    run_salt_bootstrap_ salt $@
}

run_mastersalt_bootstrap() {
    run_salt_bootstrap_ mastersalt $@
}


install_mastersalt_daemons() {
    # --------- check if we need to run mastersalt setup's
    RUN_MASTERSALT_BOOTSTRAP=""
    if [[ -n "$IS_MASTERSALT" ]];then
        if [[ -n "$IS_MASTERSALT_MASTER" ]];then
            if  [[ ! -e "$MCONF_PREFIX/pki/master/master.pem" ]]\
                || [[ ! -e "$MCONF_PREFIX/master.d/00_global.conf" ]];then
                RUN_MASTERSALT_BOOTSTRAP="1"
            fi
        fi
        if     [[ ! -e "$MCONF_PREFIX" ]]\
            || [[ ! -e "$MCONF_PREFIX/minion.d/00_global.conf" ]]\
            || [[ ! -e "$MCONF_PREFIX/pki/minion/minion.pem" ]]\
            || [[ -e "$MASTERSALT_MS/.reboostrap" ]]\
            || [[ "$(grep makina-states.controllers.mastersalt_ "$MCONF_PREFIX/grains" |wc -l)" == "0" ]]\
            || [[ ! -e "$BIN_DIR/mastersalt" ]]\
            || [[ ! -e "$BIN_DIR/mastersalt-master" ]]\
            || [[ ! -e "$BIN_DIR/mastersalt-key" ]]\
            || [[ ! -e "$BIN_DIR/mastersalt-ssh" ]]\
            || [[ ! -e "$BIN_DIR/mastersalt-syndic" ]]\
            || [[ ! -e "$BIN_DIR/mastersalt-cp" ]]\
            || [[ ! -e "$BIN_DIR/mastersalt-minion" ]]\
            || [[ ! -e "$BIN_DIR/mastersalt-call" ]]\
            || [[ ! -e "$BIN_DIR/mastersalt" ]]\
            || [[ ! -e "$MCONF_PREFIX/pki/minion/minion.pem" ]];then
            if [[ -e "$MASTERSALT_MS/.reboostrap" ]];then
                rm -f "$MASTERSALT_MS/.rebootstrap"
            fi
            RUN_MASTERSALT_BOOTSTRAP="1"
        fi
    fi
    debug_msg "mastersalt:"
    debug_msg "RUN_MASTERSALT_BOOTSTRAP: $RUN_MASTERSALT_BOOTSTRAP"
    debug_msg "grains: $(grep makina-states.controllers.mastersalt_ "$MCONF_PREFIX/grains" |wc -l)"
    debug_msg $(ls  "$BIN_DIR/mastersalt-master" "$BIN_DIR/mastersalt-key" \
        "$BIN_DIR/mastersalt-minion" "$BIN_DIR/mastersalt-call" \
        "$BIN_DIR/mastersalt" "$MCONF_PREFIX" \
        "$MCONF_PREFIX/pki/minion/minion.pem" 1>/dev/null)

    # --------- MASTERSALT
    # in case of redoing a bootstrap for wiring on mastersalt
    # after having already bootstrapped using a regular salt
    # installation,
    # we will run the specific mastersalt parts to wire
    # on the global mastersalt
    if [[ -n "$RUN_MASTERSALT_BOOTSTRAP" ]];then
        ds=y

        # kill salt running daemons if any
        if [[ -n "$IS_MASTERSALT_MASTER" ]];then
            killall_local_mastersalt_masters
        fi
        if [[ -n "$IS_MASTERSALT_MINION" ]];then
            killall_local_mastersalt_minions
        fi

        # run mastersalt master+minion boot_nodetype bootstrap
        run_mastersalt_bootstrap $mastersalt_bootstrap_nodetype

        # run mastersalt master setup
        if [[ -n "$IS_MASTERSALT_MASTER" ]];then
            run_mastersalt_bootstrap $mastersalt_bootstrap_master
        fi

        if [[ -n "$IS_MASTERSALT_MINION" ]];then
            # run mastersalt minion setup
            run_mastersalt_bootstrap $mastersalt_bootstrap_minion
        fi

        # kill mastersalt running daemons if any
        # restart mastersalt salt-master after setup
        if [[ -n "$IS_MASTERSALT_MASTER" ]];then
            debug_msg "Forcing mastersalt master restart"
            restart_local_mastersalt_masters
            sleep 10
        fi
        if [[ -n "$IS_MASTERSALT_MINION" ]];then
        # restart mastersalt minion
            debug_msg "Forcing mastersalt minion restart"
            restart_local_mastersalt_minions
        fi
        SALT_BOOT_NOW_INSTALLED="y"
    else
        if [[ -n "$IS_MASTERSALT" ]];then bs_log "Skip MasterSalt installation, already done";fi
    fi
}

install_mastersalt_env() {
    if [[ -z "$IS_MASTERSALT" ]];then return;fi
    install_mastersalt_daemons
    lazy_start_mastersalt_daemons
    make_mastersalt_association
}

install_salt_env() {
    if [[ -z "$IS_SALT" ]];then return;fi
    # XXX: important mastersalt must be configured before salt
    # to override possible local settings.
    install_salt_daemons
    lazy_start_salt_daemons
    make_association
    # --------- stateful state return: mark as already installed
    if [[ -z "$ds" ]];then
        echo 'changed=false comment="already bootstrapped"'
    fi
}

get_module_args() {
    arg=""
    for i in $@;do
        arg="$arg -m \"$i/_modules\""
    done
    echo $arg
}

# --------- HIGH-STATES

highstate_in_mastersalt_env() {
    # IMPORTANT: MASTERSALT BEFORE SALT !!!
    if [[ -z "$SALT_BOOT_SKIP_HIGHSTATES" ]]\
        && [[ -z "$MASTERSALT_BOOT_SKIP_HIGHSTATE" ]];then
        bs_log "Running makina-states highstate for mastersalt"
        bs_log "    export MASTERSALT_BOOT_SKIP_HIGHSTATE=1 to skip (dangerous)"
        LOCAL=""
        if [[ "$(mastersalt_ping_test)" != "0" ]];then
            LOCAL="--local $LOCAL"
            bs_yellow_log " [bs] mastersalt highstate running offline !"
        fi
        mastersalt_call_wrapper $LOCAL state.highstate
        if [[ -n "$SALT_BOOT_DEBUG" ]];then cat $SALT_BOOT_OUTFILE;fi
        warn_log
        if [[ "$last_salt_retcode" != "0" ]];then
            bs_log "Failed highstate for mastersalt"
            exit -1
        fi
        echo "changed=yes comment='mastersalt highstate run'"
    else
        echo "changed=false comment='mastersalt highstate skipped'"
    fi
}

highstate_in_salt_env() {
    if [[ -z "$SALT_BOOT_SKIP_HIGHSTATES" ]]\
        && [[ -z "$SALT_BOOT_SKIP_HIGHSTATE" ]];then
        bs_log "Running makina-states highstate"
        bs_log "    export SALT_BOOT_SKIP_HIGHSTATE=1 to skip (dangerous)"
        LOCAL=""
        if [[ "$(salt_ping_test)" != "0" ]];then
            bs_yellow_log " [bs] salt highstate running offline !"
            LOCAL="--local $LOCAL"
        fi
        salt_call_wrapper $LOCAL state.highstate
        if [[ "$last_salt_retcode" != "0" ]];then
            bs_log "Failed highstate"
            warn_log
            exit -1
        fi
        echo "changed=yes comment='salt highstate run'"
    else
        echo "changed=false comment='salt highstate skipped'"
    fi
    if [[ -n "$SALT_BOOT_DEBUG" ]];then cat $SALT_BOOT_OUTFILE;fi
    warn_log

    # --------- stateful state return: mark as freshly installed
    if [[ -n "$SALT_BOOT_NOW_INSTALLED" ]];then
        warn_log
        echo "changed=yes comment='salt installed and configured'"
    fi

}

run_highstates() {
    if [[ -n "$IS_SALT" ]];then
        highstate_in_salt_env
    fi
    if [[ -n "$IS_MASTERSALT" ]];then
        highstate_in_mastersalt_env
    fi
}

# -------------- MAKINA PROJECTS

maybe_install_projects() {
    if [[ -n "$PROJECT_URL" ]];then
        bs_log "Projects managment"
        project_grain="makina-states.projects.${PROJECT_NAME}.boot.top"
        BR=""
        if [[ -n "$PROJECT_BRANCH" ]];then
            BR="-b $PROJECT_BRANCH"
        fi
        FORCE_PROJECT_TOP="${FORCE_PROJECT_TOP:-}"
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
                bs_log "Failed to download project from $PROJECT_URL, or maybe the salt states branch $PROJECT_BRANCH does not exist"
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
        if [[ -f "$SALT_ROOT/${PROJECT_TOPSLS_DEFAULT}"  ]] && [[ -z ${PROJECT_TOPSLS} ]];then
            PROJECT_TOPSLS="$PROJECT_TOPSLS_DEFAULT"
        fi
        PROJECT_TOPSTATE="$(echo ${PROJECT_TOPSLS}|sed -re 's/\//./g' -e 's/\.sls//g')"
        if [[ ! -d "$PROJECT_PILLAR_PATH" ]];then
            mkdir -p "$PROJECT_PILLAR_PATH"
            debug_msg "Creating pillar container in $PROJECT_PILLAR_PATH"
        fi
        if [[ ! -d "$PROJECTS_PILLAR_PATH" ]];then
            mkdir -p "$PROJECTS_PILLAR_PATH"
            debug_msg "Creating $MAKINA_PROJECTS pillar container in $SALT_PILLAR"
        fi
        if [[ ! -e "$PROJECT_PILLAR_LINK" ]];then
            debug_msg "Linking project $PROJECT_NAME pillar in $SALT_PILLAR"
            echo ln -sf "$PROJECT_PILLAR_PATH" "$PROJECT_PILLAR_LINK"
            ln -sf "$PROJECT_PILLAR_PATH" "$PROJECT_PILLAR_LINK"
        fi
        if [[ ! -e "$PROJECT_PILLAR_FILE" ]];then
            if [[ ! -e "$PROJECT_SALT_PATH/PILLAR.sample.sls" ]];then
                debug_msg "Creating empty project $PROJECT_NAME pillar in $PROJECT_PILLAR_FILE"
                touch "$PROJECT_SALT_PATH/PILLAR.sample.sls"
            fi
            debug_msg "Linking project $PROJECT_NAME pillar in $PROJECT_PILLAR_FILE"
            ln -sf "$PROJECT_SALT_PATH/PILLAR.sample.sls" "$PROJECT_PILLAR_FILE"
        fi
        if [[ $(grep -- "- $PROJECT_PILLAR_STATE" $SALT_PILLAR/top.sls|wc -l) == "0" ]];then
            debug_msg "including $PROJECT_NAME pillar in $SALT_PILLAR/top.sls"
            sed -re "/('|\")\*('|\"):/ {
a\    - $PROJECT_PILLAR_STATE
}" -i $SALT_PILLAR/top.sls
        fi
        if [[ "$(get_grain $project_grain)" != *"True"* ]] || [[ -n $FORCE_PROJECT_TOP ]];then
            if [[ -n $PROJECT_TOPSLS ]];then
                SALT_BOOT_LOGFILE="$PROJECT_SALT_PATH/.salt_top_log.log"
                SALT_BOOT_OUTFILE="$PROJECT_SALT_PATH/.salt_top_out.log"
                bs_log "Running salt Top state: $PROJECT_URL@$PROJECT_BRANCH[$PROJECT_TOPSLS]"
                salt_call_wrapper state.sls "$PROJECT_TOPSTATE"
                if [[ -n "$SALT_BOOT_DEBUG" ]];then
                    cat $SALT_BOOT_OUTFILE;
                fi
                if [[ "$last_salt_retcode" != "0" ]];then
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
        if [[ $(grep -- "- $PROJECT_TOPSTATE" "$SALT_ROOT/top.sls"|wc -l) == "0" ]];then
            sed -re "/('|\")\*('|\"):/ {
a\    - $PROJECT_TOPSTATE
}" -i "$SALT_ROOT/top.sls"
        fi
        bs_log "Installation finished, dont forget to install/verify:"
        bs_log "    - $PROJECT_TOPSLS in $SALT_ROOT/top.sls"
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
    for i in "$SALT_ROOT" "$MASTERSALT_ROOT";do
        if [[ "$(grep "makina-states.setup" "$i/setup.sls" 2> /dev/null|wc -l)" != "0" ]];then
            rm -rfv "$i/setup.sls"
        fi
    done
    for i in "${SALT_MS}" "$MASTERSALT_MS";do
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
        && [[ -e "$SALT_PILLAR/mastersalt.sls" ]] \
        && [[ -e ${BIN_DIR}/mastersalt ]];then
        bs_log "copy old pillar to new $MASTERSALT_PILLAR"
        cp -rf "$SALT_PILLAR" "$MASTERSALT_PILLAR"
        rm -vf "$SALT_PILLAR/mastersalt.sls"
        if [[ -e "$MASTERSALT_PILLAR/salt.sls" ]];then
            rm -vf "$MASTERSALT_PILLAR/salt.sls"
        fi
        sed -re "/^\s*- salt$/d" -i "$MASTERSALT_PILLAR/top.sls"
        sed -re "/^\s*- mastersalt$/d" -i "$SALT_PILLAR/top.sls"

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

bs_help() {
    title=$1
    shift
    help=$1
    shift
    default=$1
    shift
    opt=$1
    shift
    msg="     ${YELLOW}${title} ${NORMAL}${CYAN}${help}${NORMAL}"
    if [[ -z $opt ]];then
        msg="$msg ${YELLOW}(mandatory)${NORMAL}"
    fi
    if [[ -n $default ]];then
        msg="$msg ($default)"
    fi
    echo -e "$msg"
}

exemple() {
    sname="./$(basename $0)"
    echo -e "     ${YELLOW}${sname}${1} ${CYAN}${2}${NORMAL}"

}

usage() {
    bs_log "$0:"
    echo
    bs_yellow_log "This script will install salt minion(s) and maybe master(s) on different flavors (salt/mastersalt) on top of makina-states"
    bs_yellow_log "This script installs by default a salt master/minion pair on localhost"
    bs_yellow_log "This script can also install a mastersalt minion and maybe a mastersalt master."
    bs_yellow_log "It will install first what the server needed as requirements and system settings, then the saltstate stuff"
    if [[ -n $SALT_LONG_HELP ]];then
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
    bs_help "-d|--debug:" "debug/verbose mode" "NOT SET" y
    bs_help "--debug-level <level>:" "debug level (quiet|all|info|error)" "NOT SET" y

    echo;echo
    bs_log "Server settings:"
    bs_help "-n|--nodetype <nt>:" "Nodetype to install into (devhost | server | dockercontainer | lxcontainer | vm | vagrantvm )" "$SALT_NODETYPE" "y"
    echo
    bs_log "Salt settings:"
    bs_help "--no-salt:" "Do not install salt daemons" "" y
    bs_help "-no-M|--no-salt-master:" "Do not install a salt master" "$IS_SALT_MASTER" y
    bs_help "-m|--minion-id:" "Minion id" "$SALT_MINION_ID" y
    bs_help "--salt-master-dns <hostname>:" "DNS of the salt master" "$SALT_MASTER_DNS" y
    bs_help "--salt-master-port <port>:"        "Port of the salt master" "$MASTERSALT_MASTER_PORT" y
    echo
    bs_log "Mastersalt settings (if any):"
    echo -e "    ${YELLOW} by default, we only install a minion, unless you add -MM${NORMAL}"
    bs_help "--mastersalt <dns>:" "DNS of the mastersalt master" "$MASTERSALT_MASTER_DNS" y
    bs_help "--mastersalt-master-port <port>:"  "Port of the mastersalt master" "$MASTERSALT_MASTER_PORT" y
    bs_help "--no-mastersalt:" "Do not install mastersalt daemons" "" y
    bs_help "-NN|--mastersalt-minion:" "install a mastersalt minion" "$IS_MASTERSALT_MINION" y
    bs_help "-MM|--mastersalt-master:" "install a mastersalt master" "$IS_MASTERSALT_MASTER" y
    echo
    bs_log "Project settings (if any):"
    bs_help "-u|--project-url <url>:" "project url to get to install this project (set to blank to only install makina-states)"
    bs_help "-B|--project-name <name>:" "Project name" "" "y"
    bs_help "-b|--project-branch <branch>:" "salt branch to install the project"  "$PROJECT_BRANCH" y

    if [[ -n $SALT_LONG_HELP ]];then
        echo
        bs_log "Advanced settings:"
        bs_help "--salt-minion-dns <dns>:" "DNS of the salt minion" "$SALT_MINION_DNS" "y"
        bs_help "-g|--makina-states-url <url>:" "makina-states url" "$STATES_URL" y
        bs_help "-r|--root <path>:" "/ path" "$ROOT"
        bs_help "--salt-root <path>:" "Salt root installation path" "$SALT_ROOT" y
        bs_help "--conf-root <path>:" "Salt configuration container path" "$CONF_ROOT" y
        bs_help "-p|--prefix <path>:" "prefix path" "$PREFIX" y
        bs_help "-P|--pillar <path>:" "pillar path" "$SALT_PILLAR" y
        bs_help "-M|--salt-master:" "install a salt master" "$IS_SALT_MASTER" y
        bs_help "-N|--salt-minion:" "install a salt minion" "$IS_SALT_MINION" y
        bs_help "-no-N|--no-salt-minion:" "Do not install a salt minion" "$IS_SALT_MINION" y
        #bs_help "-mac|--master-controller <controller>:" "makina-states controller to use for the master" "$SALT_MASTER_CONTROLLER" y
        #bs_help "-mic|--minion-controller <controller>:" "makina-states controller to use for the minion" "$SALT_MINION_CONTROLLER" y
        bs_help "--salt-master-publish-port:" "Salt master publish port" "$SALT_MASTER_PUBLISH_PORT" y

        bs_log "  Mastersalt settings (if any):"
        bs_help "-nn|--mastersalt-nodetype <nt>:" "Nodetype to install mastersalt into" "$MASTERSALT_NODETYPE" "y"
        bs_help "--mconf-root <path>:" "Mastersalt configuration container path" "$CONF_ROOT" y
        bs_help "--mastersalt-root <path>:" "MasterSalt root installation path" "$SALT_ROOT" y
        bs_help "-PP|--mastersalt-pillar <path>:" "mastersalt pillar path" "$MASTERSALT_PILLAR"  y
        bs_help "--mastersalt-minion-dns <dns>:"  "DNS of the mastersalt minion" "$MASTERSALT_MINION_DNS" y
        bs_help "--mastersalt-master-publish-port <port>:" "MasterSalt master publish port" "$MASTERSALT_MASTER_PUBLISH_PORT" y
        #bs_help "-mmac|--mastersalt-master-controller <controller>:" "makina-states controller to use for the mastersalt master" "$MASTERSALT_MINION_CONTROLLER"   y
        #bs_help "-mmic|--mastersalt-minion-controller <controller>:" "makina-states controller to use for the mastersalt minion" "$MASTERSALT_MASTER_CONTROLLER"  y
        bs_help "-no-MM|--no-mastersalt-master:" "do not install a mastersalt master" "$IS_MASTERSALT_MASTER" y
        bs_help "-no-NN|--no-mastersalt-minion:" "do not install a mastersalt minion" "$IS_MASTERSALT_MINION" y

        bs_log "  Project settings (if any):"
        bs_help "--projects-path <path>:" "projects root path" "$PROJECTS_PATH" y
        bs_help "--project-top <sls>:" "project SLS file to execute"  "$PROJECT_TOPSLS" y
    fi
}

parse_cli_opts() {
    set_vars # to collect defaults for the help message
    args=$@
    PARAM=""
    while true
    do
        sh=1
        if [[ "$1" == "$PARAM" ]];then
            break
        fi
        case "$1" in
            -h|--help) USAGE=1
                ;;
            -d|--debug) SALT_BOOT_DEBUG=y
                ;;
            --debug-level) SALT_BOOT_DEBUG_LEVEL=$2;sh=2
                ;;
            -l|--long-help) SALT_LONG_HELP=1;USAGE=1;
                ;;
            -S|--skip-checkouts) SALT_BOOT_SKIP_CHECKOUTS=y
                ;;
            -s|--skip-highstates) SALT_BOOT_SKIP_HIGHSTATES=y
                ;;
            -C|--no-confirm) SALT_BOOT_NOCONFIRM=y
                ;;
            -M|--salt-master) IS_SALT_MASTER=y
                ;;
            -N|--salt-minion) IS_SALT_MINION=y
                ;;
            -MM|--mastersalt-master) IS_MASTERSALT_MASTER=y
                ;;
            -NN|--mastersalt-minion) IS_MASTERSALT_MINION=y
                ;;
            -no-M|--no-salt-master) FORCE_IS_SALT_MASTER="no"
                ;;
            -no-N|--no-salt-minion) FORCE_IS_SALT_MINION="no"
                ;;
            --no-salt) FORCE_IS_SALT="no"
                ;;
            --no-mastersalt) FORCE_IS_MASTERSALT="no"
                ;;
            -no-MM|--no-mastersalt-master) FORCE_IS_MASTERSALT_MASTER="no"
                ;;
            -no-NN|--no-mastersalt-minion) FORCE_IS_MASTERSALT_MINION="no"
                ;;
            -m|--minion-id) SALT_MINION_ID=$2;sh=2
                ;;
            -mac|--master-controller) SALT_MASTER_CONTROLLER=$2;sh=2
                ;;
            -mmac|--mastersalt-master-controller) MASTERSALT_MASTER_CONTROLLER=$2;sh=2
                ;;
            -mic|--minion-controller) SALT_MINION_CONTROLLER=$2;sh=2
                ;;
            -mmic|--mastersalt-minion-controller) MASTERSALT_MINION_CONTROLLER=$2;sh=2
                ;;
            --salt-master-dns) SALT_MASTER_DNS=$2;sh=2
                ;;
            --salt-minion-dns) SALT_MINION_DNS=$2;sh=2
                ;;
            --mastersalt-minion-dns) MASTERSALT_MINION_DNS=$2;sh=2
                ;;
            --salt-master-port) SALT_MASTER_PORT=$2;sh=2
                ;;
            --salt-master-publish-port) SALT_MASTER_PUBLISH_PORT=$2;sh=2
                ;;
            --mastersalt-master-port) MASTERSALT_MASTER_PORT=$2;sh=2
                ;;
            --mastersalt-master-publish-port) MASTERSALT_MASTER_PUBLISH_PORT=$2;sh=2
                ;;
            -n|--nodetype) SALT_NODETYPE=$2;sh=2
                ;;
            -nn|--mastersalt-nodetype) MASTERSALT_NODETYPE=$2;sh=2
                ;;
            -g|--makina-states-url) STATES_URL="$2";sh=2
                ;;
            --mastersalt) MASTERSALT="$2";sh=2
                ;;
            -r|--root) ROOT=$2;sh=2
                ;;
            --salt-root) SALT_ROOT=$2;sh=2
                ;;
            --mastersalt-root) MASTERSALT_ROOT=$2;sh=2
                ;;
            --conf-root) CONF_ROOT=$2;sh=2
                ;;
            --mconf-root) MCONF_ROOT=$2;sh=2
                ;;
            -p|--prefix) PREFIX=$2;sh=2
                ;;
            -P|--pillar) SALT_PILLAR=$2;sh=2
                ;;
            -PP|--mastersalt-pillar) MASTERSALT_PILLAR=$2;sh=2
                ;;
            -u|--project-url) PROJECT_URL=$2;sh=2
                ;;
            -B|--project-name) PROJECT_NAME=$2;sh=2
                ;;
            -b|--project-branch) PROJECT_BRANCH=$2;sh=2
                ;;
            --project-top) PROJECT_TOPSLS=$2;sh=2
                ;;
            --projects-path) PROJECTS_PATH=$2;sh=2
                ;;
            *) break
                ;;
        esac    # --- end of case ---
        PARAM="$1"
        OLD_ARG=$1
        for i in $(seq $sh);do
            shift
            if [[ "$1" == "$OLD_ARG" ]];then
                break
            fi
        done
        if [[ -z "$1" ]];then
            break
        fi
    done
    if [[ -n $USAGE ]];then
        usage
        exit 0
    fi
}

if [[ -z $SALT_BOOT_AS_FUNCS ]];then
    parse_cli_opts $LAUNCH_ARGS
    if [[ "$(dns_resolve localhost)" == "$DNS_RESOLUTION_FAILED" ]];then
        die_in_error "$DNS_RESOLUTION_FAILED"
    fi
    set_vars # real variable affectation
    recap
    cleanup_old_installs
    setup_and_maybe_update_code
    setup_virtualenv
    install_buildouts
    create_salt_skeleton
    install_mastersalt_env
    install_salt_env
    run_highstates
    maybe_install_projects
    exit 0
fi
# vim:set et sts=5 ts=4 tw=0:

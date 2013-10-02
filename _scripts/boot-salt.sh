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
base_packages=""
base_packages="$base_packages build-essential m4 libtool pkg-config autoconf gettext bzip2"
base_packages="$base_packages groff man-db automake libsigc++-2.0-dev tcl8.5 git python-dev"
base_packages="$base_packages swig libssl-dev libzmq-dev libyaml-dev debconf-utils python-virtualenv"

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
    for i in $base_packages;do
        if ! dpkg -l $i &> /dev/null;then
            to_install="$to_install $i"
        fi
    done
    if [[ -n $to_install ]];then
        echo "Installing pre requisites: $to_install"
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
salt_call() {
    outf="$SALT_OUTFILE"
    logf="$SALT_LOGFILE"
    rm -rf "$outf" "$logf" 2> /dev/null
    salt-call --retcode-passthrough --out=yaml --out-file="$outf" --log-file="$logf" -lquiet $@
    ret=$?
    #echo "result: false">>$outf
    if [[ $ret != 0 ]] && [[ $ret != 2 ]];then
        ret=100
    elif grep  -q "No matching sls found" "$logf";then
        ret=101
        no_check_output=y
    elif egrep -q "\[salt.state       \]\[ERROR   \]" "$logf";then
        ret=102
        no_check_output=y
    else
        if egrep -q "result: false" "$outf";then
            ret=104
        else
            ret=0
        fi
    fi
    #rm -rf "$outf" "$logf" 2> /dev/null
    echo $ret
}
for i in "$PILLAR" "$ROOT";do
    if [[ ! -d $i ]];then
        mkdir -pv $i
    fi
done
i_prereq || die_in_error "Failed install rerequisites"
if [[ ! -d "$MS/.git" ]];then
    git clone "$STATES_URL" "$MS" || die_in_error "Failed to download makina-states"
else
    cd $MS && git pull || die_in_error "Failed to update makina-states"
fi
cd $MS
if     [[ ! -e "$MS/bin/activate" ]] \
    || [[ ! -e "$MS/lib" ]] \
    || [[ ! -e "$MS/include" ]] \
    ;then
    echo "Creating virtualenv"
    virtualenv --no-site-packages --unzip-setuptools . &&\
    . bin/activate &&\
    easy_install -U setuptools &&\
    deactivate
fi
if [[ -e bin/activate ]];then
    . bin/activate
fi
if    [[ ! -e "$MS/bin/buildout" ]]\
   || [[ ! -e "$MS/parts" ]] \
   || [[ ! -e "$MS/develop-eggs" ]] \
    ;then
    echo "Launching buildout bootstrap for salt initialisation"
    python bootstrap.py
    ret=$?
    if [[ "$ret" != "0" ]];then
        rm -rf "$MS/parts" "$MS/develop-eggs"
        die $ret "Failed bootstrap"
    fi
fi
if    [[ ! -e "$MS/bin/buildout" ]]\
    || [[ ! -e "$MS/bin/salt-ssh" ]]\
    || [[ ! -e "$MS/bin/salt" ]]\
    || [[ ! -e "$MS/bin/mypy" ]]\
    || [[ ! -e "$MS/.installed.cfg" ]]\
    || [[ ! -e "$MS/src/salt/setup.py" ]]\
    || [[ ! -e "$MS/src/docker/setup.py" ]]\
    || [[ ! -e "$MS/src/m2crypto/setup.py" ]]\
    || [[ ! -e "$MS/src/SaltTesting/setup.py" ]]\
    ;then
    echo "Launching buildout for salt initialisation"
    bin/buildout || die_in_error "Failed buildout"
    ret=$?
    if [[ "$ret" != "0" ]];then
        rm -rf "$MS/.installed.cfg"
        die $ret "Failed buildout"
    fi
fi
#exit -1
if [[ ! -f /srv/pillar/top.sls ]];then
    cat > /srv/pillar/top.sls << EOF
base:
  '*':
EOF
fi
if [[ $(grep -- "- salt" /srv/pillar/top.sls|wc -l) == "0" ]];then
    sed -re "/('|\")\*('|\"):/ {
a\     - salt
}" -i /srv/pillar/top.sls
fi
if [[ ! -f /srv/pillar/salt.sls ]];then
    cat > /srv/pillar/salt.sls << EOF
salt:
  minion:
    master: 127.0.0.1
    interface: 127.0.0.1
  master:
    interface: 127.0.0.1
EOF
fi
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
if [[ ! -f "$ROOT/.boot_vebootstrap_salt" ]];then
    ds=y
    cd $MS
    ps aux|egrep "salt-(master|minion|syndic)" |awk '{print $2}'|xargs kill -9
    echo "Boostrapping salt"
    ret=$(salt_call --local state.sls $bootstrap)
    if [[ $ret != 0 ]];then
        echo "Failed bootstrap: $bootstrap !"
        exit $ret
    fi
    echo "Waiting for key to be accepted"
    sleep 10
    ps aux|grep salt-minion|awk '{print $2}'|xargs kill -9
    service salt-minion restart
    salt-key -A -y
    ret=$?
    if [[ $ret != 0 ]];then
        echo "Failed accepting keys"
        exit $ret
    fi
    cat $SALT_OUTFILE
    echo "changed=yes comment='salt installed'"
    touch "$ROOT/.boot_vebootstrap_salt"
    if [[ "$bootstrap" == "mastersalt" ]];then
        touch "$ROOT/.boot_vebootstrap_mastersalt"
    fi
fi
# in case of redoing a bootstrap for wiring on mastersalt
# after having already bootstrapped using a regular salt
# installation,
# we will run the specific mastersalt parts to wire
# on the global mastersalt
if  [[ ! -e "$ROOT/.boot_vebootstrap_mastersalt" ]] \
    && [[ "$bootstrap" == "mastersalt" ]];then
    ds=y
    cd $MS
    ps aux|egrep "salt-(master|minion|syndic)" |awk '{print $2}'|xargs kill -9
    echo "Boostrapping salt"
    ret=$(salt_call --local state.sls $bootstrap)
    if [[ $ret != 0 ]];then
        echo "Failed bootstrap: $bootstrap !"
        exit $ret
    fi
    ps aux|grep salt-minion|grep mastersalt|awk '{print $2}'|xargs kill -9
    service mastersalt-minion restart
    cat $SALT_OUTFILE
    echo "changed=yes comment='mastersalt installed'"
    touch "$ROOT/.boot_vebootstrap_mastersalt"
fi
if [[ -z $ds ]];then
    echo 'changed="false" comment="already bootstrapped"'
fi
if [[ -n $PROJECT_URL ]];then
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
        echo "Cloning  $PROJECT_URL / $PROJECT_BRANCH"
        git clone $BR "$PROJECT_URL" "${project_tmpdir}"
        ret=$?
        if [[ $ret != 0 ]];then
            echo "Failed to download project from $PROJECT_URL, or maybe the saltstack branch $PROJECT_BRANCH does not exist"
            exit -1
        fi
        rsync -az "${project_tmpdir}/" "$ROOT/"
        cd $ROOT
        if [[ -f setup.sls  ]] && [[ -z ${PROJECT_SETUPSTATE} ]];then
            PROJECT_SETUPSTATE=setup
        fi
        if [[ -n $PROJECT_SETUPSTATE ]];then
            echo "Luanching saltstack setup ($PROJECT_SETUPSTATE) for $PROJECT_URL"
            ret=$(salt_call --local state.sls $PROJECT_SETUPSTATE)
            cat $SALT_OUTFILE
            if [[ $ret != 0 ]];then
                echo "Failed to run setup.sls"
                exit -1
            fi
        fi
        echo "Luanching saltstack top state ($PROJECT_TOPSTATE) for $PROJECT_URL"
        ret=$(salt_call --local $PROJECT_TOPSTATE)
        if [[ $ret == 0 ]];then
            cat $SALT_OUTFILE
            echo  "changed=\"yes\" comment=\"$PROJECT_URL // $PROJECT_BRANCH // $PROJECT_TOPSTATE Installed\""
            touch "$project_mark"
        fi
    fi
fi
# vim:set et sts=5 ts=4 tw=0:

#!/usr/bin/env bash
export PATH=/srv/salt/makina-states/bin:$PATH
MASTERSALT="${MASTERSALT:-mastersalt.makina-corpus.net}"
MASTERSALT_PORT="${MASTERSALT_PORT:-4506}"
PILLAR=${PILLAR:-/srv/salt}
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
    echo "Installing pre requisites"
    echo 'changed="yes" comment="prerequisites installed"'
    apt-get update && apt-get install -y build-essential m4 libtool pkg-config autoconf gettext bzip2 groff man-db automake libsigc++-2.0-dev tcl8.5 git python-dev swig libssl-dev libzmq-dev libyaml-dev
}
die_in_error() {
    ret=$?
    if [[ $ret != 0 ]];then
        echo $@
        exit $ret
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
if [[ ! -f "$ROOT/.boot_prereq" ]];then
    i_prereq || die_in_error "Failed install rerequisites"
    touch "$ROOT/.boot_prereq"
fi
if [[ ! -d "$MS/.git" ]];then
    git clone "$STATES_URL" "$MS" || die_in_error "Failed to download makina-states"
else
    git pull
fi
cd $MS
if [[ ! -f "$ROOT/.boot_bootstrap" ]];then
    echo "Launching buildout bootstrap for salt initialisation"
    python bootstrap.py || die_in_error "Failed bootstrap"
    touch "$ROOT/.boot_bootstrap"
fi
if [[ ! -f "$ROOT/.boot_buildout" ]];then
    echo "Launching buildout for salt initialisation"
    bin/buildout || die_in_error "Failed buildout"
    touch "$ROOT/.boot_buildout"
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
if [[ ! -f "$ROOT/.boot_bootstrap_salt" ]];then
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
    touch "$ROOT/.boot_bootstrap_salt"
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
# vim:set et sts=5 ts=4 tw=80:

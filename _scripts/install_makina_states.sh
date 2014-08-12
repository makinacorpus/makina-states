#!/usr/bin/env bash
SALT_ROOT="${1:-/srv/salt}"
MS_URL="${MS_URL:-https://github.com/makinacorpus/makina-states.git}"
MS_BRANCH="${MS_BRANCH:-stable}"
MS_PATH="${MS_PATH:-${SALT_ROOT}/makina-states}"
SALT_PYTHON="${SALT_PYTHON:-}"
TO_DIE=""
SALT_BIN="$(which salt 2>/dev/null)"
salt_python=$(head -n 1 "${SALT_BIN}"|sed -re "s/^#!//g"|grep python)
pymods=""
die_(){
    code=$1
    shift
    echo "$@"
    echo "exit: ${code}"
    exit "${code}"
}
die() {
    die_ 1 $@
}
trigger_die() {
    TO_DIE="1"
    echo "${@}"
}
trigger_py_die() {
    pymods="${pymods} ${@}"
    trigger_die "missing python package: ${@}, please install"
}
check_die() {
    if [ "x${TO_DIE}" != "x" ];then
        die ${@:-"die triggered"}
    fi
}
set_python() {
    if [ "x${SALT_PYTHON}" = "x" ];then
        if [ ! -e "${salt_python}" ];then
            SALT_PYTHON="$(which python)"
        else
            SALT_PYTHON="${salt_python}"
        fi
    fi
    if [ ! -e "${SALT_PYTHON}" ];then
        die "Can't find python interpreter"
    fi
}
check_salt() {
    if [ ! -e "${SALT_BIN}" ];then
        die "salt is not installed"
    fi
    if [ ! -e "${SALT_ROOT}" ];then
        die "invalid salt root: $SALT_ROOT"
    fi
    echo "Salt install in place"
}
check_ms() {
    if [ ! -e "${MS_PATH}/.git" ];then
        git clone "${MS_URL}" "${MS_PATH}" || die "cant install makina-states"
        cd "${MS_PATH}"
        git reset --hard "remotes/origin/${MS_BRANCH}" || git reset --hard "${MS_BRANCH}"
        if [ "x${?}" != "x0" ];then
            die "Checkout to branch ${MS_BRANCH} failed"
        fi
    fi
    echo "Makina-States install in place"
}
install_pip() {
    python -c "import urllib;print urllib.urlopen('https://bootstrap.pypa.io/get-pip.py').read()" | python
    if [ "x${?}" != "x0" ];then
        die "pip install failed"
    fi
    echo "pip installed"
}
verbose_call() {
    echo "Running ${@}"
    "${@}"
}
check_python() {
    set_python
    pip >/dev/null 2>&1 || install_pip
    "${SALT_PYTHON}" -c "import concurrent" >/dev/null 2>&1\
        || trigger_py_die "futures"
    "${SALT_PYTHON}" -c "import dns" >/dev/null 2>&1\
        || trigger_py_die "dnspython"
    "${SALT_PYTHON}" -c "import yaml" >/dev/null 2>&1\
        || trigger_py_die "pyyaml"
    "${SALT_PYTHON}" -c "import OpenSSL" >/dev/null 2>&1\
        || trigger_py_die "pyOpenSSL"
    "${SALT_PYTHON}" -c "import libcloud" >/dev/null 2>&1\
        || trigger_py_die "apache-libcloud"
    "${SALT_PYTHON}" -c "import docker" >/dev/null 2>&1\
        || trigger_py_die "docker-py"
    "${SALT_PYTHON}" -c "import Crypto" >/dev/null 2>&1\
        || trigger_py_die "pycrypto"
    "${SALT_PYTHON}" -c "import zmq" >/dev/null 2>&1\
        || trigger_py_die "pyzmq"
    for i in ipaddr ipwhois tornado\
        pyasn1 requests urllib3 salt salttesting\
        ;do
        "${SALT_PYTHON}" -c "import ${i}" >/dev/null 2>&1\
            || trigger_py_die "${i}"
    done
    if ! "${SALT_PYTHON}" -c "import mc_states" >/dev/null 2>&1;then
        cd "${MS_PATH}" && pip install --no-deps -e .
        if [ "x${?}" != "x0" ];then
            die "Makina-States python installation failed"
        fi
    fi
    check_die "Python modules install failed, maybe time to: pip install -U ${pymods}"
    echo "Python modules dependencies OK"
}
link_modules() {
    "${SALT_PYTHON}" << EOF
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import json
modules = []
with open('${MS_PATH}/mc_states/modules_dirs.json') as fic:
    modules = json.loads(fic.read())
for i, mods in modules.items():
    target = mods[0].format(salt_root='${SALT_ROOT}')
    to_link = [a.format(salt_root='${SALT_ROOT}') for a in mods[1:]]
    to_link.reverse()
    for modules_dir in to_link:
        if not os.path.exists(modules_dir):
            continue
        for f in os.listdir(modules_dir):
            fp = os.path.join(modules_dir, f)
            if f in ['__init__.py']:
                continue
            if not (os.path.isfile(fp) and fp.endswith('.py')):
                continue
            tfp = os.path.join(target, f)
            if not os.path.isdir(target):
                print('Creating {0}'.format(target))
                os.makedirs(target)
            unlink = True
            if os.path.isfile(tfp):
                unlink = False
            if os.path.islink(tfp):
                apath = os.path.abspath(os.readlink(tfp))
                if apath != fp:
                    unlink = True
            if unlink:
                print('Removing stale: {0}'.format(tfp))
                os.unlink(tfp)
            if not os.path.exists(tfp):
                print('Linking {0} -> {1}'.format(fp, tfp))
                os.symlink(fp, tfp)
EOF
    verbose_call salt-call --local -lquiet saltutil.sync_all
    echo "Makina-States salt modules in place"
}

[ "x${INSTALL_SET_PYTHON}" != "x" ]   || set_python
[ "x${INSTALL_CHECK_SALT}" != "x" ]   || check_salt
[ "x${INSTALL_CHECK_MS}" != "x" ]     || check_ms
[ "x${INSTALL_CHECK_PYTHON}" != "x" ] || check_python
[ "x${INSTALL_LINK_MODULES}" != "x" ] || link_modules
# vim:set et sts=4 ts=4 tw=0: 

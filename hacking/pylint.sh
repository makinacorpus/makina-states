#!/usr/bin/env bash
cd $(dirname ${0})
cwd="${PWD}"
cd "${cwd}/.."
cwd="${PWD}"
abspath() {
    python -c "import os;print os.path.abspath('${1}')"
}
venv_path="$(abspath $(readlink -f "${cwd}/bin/.."))"
. bin/activate
export PYTHONPATH="${venv_path}/src/salttesting/salttesting/pylintplugins/:${PYTHONPATH}"
echo $PYTHONPATH
bin/pylint "${@}"
# vim:set et sts=4 ts=4 tw=80:

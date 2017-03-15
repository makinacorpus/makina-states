#!/usr/bin/env bash
cd $(dirname $0)
LOGGER_NAME=${LOGGER_NAME:-docbuilder}
. ../_scripts/shell_common || exit 1
if [[ -z ${SPHINX_SKIP} ]];then
    sphinx/build.sh
    die_in_error "sphinx failed"
fi
if [[ -z ${HUGO_SKIP} ]];then
    hugo/build.sh gulp
    die_in_error "sphinx failed"
fi
if [[ -z ${ASSEMBLE_SKIP} ]];then
    rsync -azv --delete \
        --exclude .git \
        hugo/public/ html/
    die_in_error "sphinx failed"
fi
# vim:set et sts=4 ts=4 tw=80:

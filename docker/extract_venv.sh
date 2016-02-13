#!/usr/bin/env bash
W="$(cd "$(dirname "${0}")" && pwd)"
export THIS_AS_FUNCS=1
. "${W}/build-scratch.sh"
img=$(echo $MS_IMAGE|sed -re "s/.*\///g"|sed "s/ubuntu/Ubuntu/gi")
dname="${img}-venv-extracter"
docker rm -f "${dname}" || /bin/true
set -e -x
docker run --rm --name="${dname}" -v "${W}/..":/makina-states \
    -e XZ_OPTS="-9e" ${MS_IMAGE}\
    tar cJf "/makina-states/docker/virtualenv-${img}.tar.xz" /srv/makina-states/venv
ret=$?
exit $?
# vim:set et sts=4 ts=4 tw=80:

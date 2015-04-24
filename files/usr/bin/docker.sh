#!/usr/bin/env bash
set -e
DOCKER=/usr/bin/docker
OCKER_OPTS=
f [ -f /etc/default/docker ]; then
   . /etc/default/docker
i
OCKER_OPTS="${DOCKER_OPTS:-"-r"}"
"$DOCKER" -d $DOCKER_OPTS 
# vim:set et sts=4 ts=4 tw=80:

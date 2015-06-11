#!/usr/bin/env bash
RED='\e[31;01m'
BLUE='\e[36;01m'
YELLOW='\e[33;01m'
GREEN='\e[32;01m'
NORMAL='\e[0m'

red() { echo "${RED}${@}${NORMAL}"; }
cyan() { echo "${CYAN}${@}${NORMAL}"; }
yellow() { echo "${YELLOW}${@}${NORMAL}"; }
die_in_error() { if [ "x${?}" != "x0" ];then echo "${@}";exit 1;fi }
# 4. rebuild any corpus projects
for i in $(find /srv/projects/ -mindepth 1 -maxdepth 1 -type d 2>/dev/null);do
    salt-call --retcode-passthrough --local\
        -linfo mc_project.deploy "$(basename ${i})" only="install,fixperms"
    die_in_error "${MS_IMAGE}-base failed to build project ${i}"
done

# ADD AFTER ANY AUTOMATED TEST PROCEDURE
# THAT ENSURE THAT THE BUILD IS SUCESSFULL
/bin/true
# vim:set et sts=4 ts=4 tw=80:

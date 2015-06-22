#!/usr/bin/env bash
# THIS SCRIPT CAN BE OVERRIDEN IN ANY MAKINA-STATES BASED IMAGES
# Copy/Edit it inside the overrides directory either:
#   - inside you image data directory, inside the image_roots/bootstrap_scripts
#   - inside your corpus based repository, inside the .salt folder

RED='\e[31;01m'
CYAN='\e[36;01m'
PURPLE='\e[33;01m'
YELLOW='\e[33;01m'
GREEN='\e[32;01m'
NORMAL='\e[0m'

purple() { echo -e "${PURPLE}${@}${NORMAL}"; }
green() { echo -e "${GREEN}${@}${NORMAL}"; }
red() { echo -e "${RED}${@}${NORMAL}"; }
cyan() { echo -e "${CYAN}${@}${NORMAL}"; }
yellow() { echo -e "${YELLOW}${@}${NORMAL}"; }
die_in_error() { if [ "x${?}" != "x0" ];then red "${@}";exit 1;fi }
warn_in_error() { if [ "x${?}" != "x0" ];then yellow "WARNING: ${@}";fi }
v_run() { green "${@}"; "${@}"; }
v_die_run() { v_run "${@}"; die_in_error "command ${@} failed"; }

echo;echo
yellow "-----------------------------------------------"
yellow "-   STAGE 3  - BUIDING                        -"
yellow "-----------------------------------------------"
echo
if [ -e /bootstrap_scripts/stage2.env ];then . /bootstrap_scripts/stage2.env;fi

# this should be sufficient to (re)build any makina-states corpus style projects
for i in $(find /srv/projects/ -mindepth 1 -maxdepth 1 -type d 2>/dev/null);do
    yellow "${MS_IMAGE}: Rebuilding project: ${i}"
    salt-call --retcode-passthrough --local\
        -linfo mc_project.deploy "$(basename ${i})" only="install,fixperms"
    die_in_error "${MS_IMAGE}: failed to build project ${i}"
done

# Add here any automated test procedure that ensure that this build is sucessful
# Exit with a non zero code to signal a failure
# <--
die_in_error "${MS_IMAGE}: failed to do post build checks"

echo
purple "--------------------"
purple "- stage3 complete  -"
purple "--------------------"
echo
# vim:set et sts=4 ts=4 tw=80:

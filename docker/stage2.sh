#!/usr/bin/env bash
# THIS SCRIPT CAN BE OVERRIDEN IN ANY MAKINA-STATES BASED IMAGES
# Copy/Edit it inside the overrides directory inside you image data directory:
# ${MS_DATA_DIR}/${MS_IMAGE}
# EG:
#  cp stage1.sh /srv/foo/makina-states/data/mycompany/mydocker/overrides/stage2.sh
#  $ED /srv/foo/makina-states/data/mycompany/mydocker/overrides/stage2.sh

RED='\e[31;01m'
CYAN='\e[36;01m'
YELLOW='\e[33;01m'
PURPLE='\e[33;01m'
GREEN='\e[32;01m'
NORMAL='\e[0m'

purple() { echo -e "${PURPLE}${@}${NORMAL}"; }
red() { echo -e "${RED}${@}${NORMAL}"; }
cyan() { echo -e "${CYAN}${@}${NORMAL}"; }
green() { echo -e "${GREEN}${@}${NORMAL}"; }
yellow() { echo -e "${YELLOW}${@}${NORMAL}"; }
die_in_error() { if [ "x${?}" != "x0" ];then red "${@}";exit 1;fi }
warn_in_error() { if [ "x${?}" != "x0" ];then yellow "WARNING: ${@}";exit 1;fi }
v_run() { green "${@}"; "${@}"; }
v_die_run() { v_run "${@}"; die_in_error "command ${@} failed"; }

echo;echo
yellow "-----------------------------------------------"
yellow "-   STAGE 2  - BUIDING                        -"
yellow "-----------------------------------------------"
echo

# 0. Save environment for subshell scripts & history
env > /bootstrap_scripts/stage2.env

# 1. Launch systemd
systemd --system &
set -x
export DEBIAN_FRONTEND=noninteractive
v_run apt-get install -y --force-yes git ca-certificates rsync acl
v_run rsync -Aa /injected_volumes/ /
# 2. Refresh makina-states code
ip route
ifconfig
if [ ! -d /srv/salt ];then mkdir -p /srv/salt;fi
bs="/srv/salt/makina-states/_scripts/boot-salt.sh"
if [ ! -e ${bs} ];then
    git clone /makina-states.git /srv/salt/makina-states &&\
    cd /srv/salt/makina-states && \
    git remote rm origin &&\
    git remote add origin "${MS_GIT_URL}" &&\
    git checkout -b "${MS_GIT_BRANCH}"
    warn_in_error "${MS_IMAGE}: problem while initing makina-states code"
fi
${bs} -C --refresh-modules
warn_in_error "${MS_IMAGE}: failed to fetch up-to-data makina-states code"

# 3. mastersalt + salt highstates & masterless mode
${bs} -C --mastersalt 127.0.0.1 -n dockercontainer\
    --local-mastersalt-mode masterless --local-salt-mode masterless
die_in_error "${MS_IMAGE}: failed installing makina-states"
echo
purple "--------------------"
purple "- stage2 complete  -"
purple "--------------------"
# 4. Run project installation, this is this script
#    which will be mostly configured by users
if [ -x /bootstrap_scripts/docker_build_stage3.sh ];then
    /bootstrap_scripts/docker_build_stage3.sh
    die_in_error "${MS_IMAGE}: Stage3 building failed"
fi
v_run getfacl -R / > /acls.txt || /bin/true
v_run touch /acls.restore
echo
purple "--------------------"
purple "- POSIX Acls saved -"
purple "--------------------"
echo
# END -- The common case is to tag back the image as a release candidate at the end
if docker inspect "${MS_IMAGE_CANDIDATE}" >/dev/null 2>&1;then
    docker rmi -f "${MS_IMAGE_CANDIDATE}"
fi
docker commit "${MS_STAGE2_NAME}" "${MS_IMAGE_CANDIDATE}" -c "CMD ${MS_COMMAND}"
die_in_error "${MS_IMAGE_CANDIDATE} failed commit"
# vim:set et sts=4 ts=4 tw=0:

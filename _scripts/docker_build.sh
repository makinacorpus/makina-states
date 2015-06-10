#!/usr/bin/env bash
# THIS SCRIPT CAN BE OVERRIDEN IN ANY MAKINA-STATES BASED IMAGES
# Do it via a volume via -v /path/to/docker_build.sh:/bootstrap_scripts/docker_build.sh
die_in_error() { if [ "x${?}" != "x0" ];then echo "${@}";exit 1;fi }
# 1. Launch systemd
systemd --system &
# 2. Refresh makina-states code
bs="/srv/salt/makina-states/_scripts/boot-salt.sh"
if [ ! -d /srv/salt ];then mkdir -p /srv/salt;fi
if [ ! -e ${bs} ];then
    git clone ${GIT_URL} -b ${BRANCH} /srv/salt/makina-states
else
    ${bs} -C --refresh-modules
fi
die_in_error "${MS_IMAGE} failed to fetch code"

# 3. mastersalt + salt highstates & masterless mode
${bs} -C --mastersalt 127.0.0.1 -n dockercontainer\
    --local-mastersalt-mode masterless --local-salt-mode masterless
die_in_error "${MS_IMAGE} failed installing makina-states"

# 4. rebuild any corpus projects
for i in $(find /srv/projects/ -mindepth 1 -maxdepth 1 -type d 2>/dev/null);do
    salt-call --retcode-passthrough --local\
        -linfo mc_project.deploy "$(basename ${i})" only="install,fixperms"
    die_in_error "${MS_IMAGE}-base failed to build project ${i}"
done

# END -- The common case is to tag back the image as a release candidate at the end
if docker inspect "${MS_IMAGE_CANDIDATE}" >/dev/null 2>&1;then
    docker rmi -f "${MS_IMAGE_CANDIDATE}"
fi
docker commit "${MS_DID}" "${MS_IMAGE_CANDIDATE}"
# vim:set et sts=4 ts=4 tw=0:

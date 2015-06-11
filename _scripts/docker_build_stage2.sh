#!/usr/bin/env bash
# THIS SCRIPT CAN BE OVERRIDEN IN ANY MAKINA-STATES BASED IMAGES
# Do it via a volume via -v /path/to/docker_build.sh:/bootstrap_scripts/docker_build.sh
die_in_error() { if [ "x${?}" != "x0" ];then echo "${@}";exit 1;fi }
# 1. Launch systemd
systemd --system &
set -x
export DEBIAN_FRONTEND=noninteractive
apt-get install -y --force-yes git ca-certificates rsync acl
rsync -Aa /forwarded_volumes/ /
# 2. Refresh makina-states code
bs="/srv/salt/makina-states/_scripts/boot-salt.sh"
ip route
ifconfig
if [ ! -d /srv/salt ];then mkdir -p /srv/salt;fi
if [ ! -e ${bs} ];then
    git clone ${MS_GIT_URL} -b ${MS_GIT_BRANCH} /srv/salt/makina-states
else
    ${bs} -C --refresh-modules
fi
die_in_error "${MS_IMAGE} failed to fetch code"

# 3. mastersalt + salt highstates & masterless mode
${bs} -C --mastersalt 127.0.0.1 -n dockercontainer\
    --local-mastersalt-mode masterless --local-salt-mode masterless
die_in_error "${MS_IMAGE} failed installing makina-states"

# 4. Run project installation, this is this script
#    which will be mostly configured by users
if [ -x /bootstrap_scripts/docker_build_stage3.sh ];then
    /bootstrap_scripts/docker_build_stage3.sh
fi

getfacl -R / > /acls.txt || /bin/true
touch /acls.restore

# END -- The common case is to tag back the image as a release candidate at the end
if docker inspect "${MS_IMAGE_CANDIDATE}" >/dev/null 2>&1;then
    docker rmi -f "${MS_IMAGE_CANDIDATE}"
fi
docker commit "${MS_DID}" "${MS_IMAGE_CANDIDATE}" -c "CMD ${MS_COMMAND}"
die_in_error "${MS_IMAGE_CANDIDATE} failed commit"
# vim:set et sts=4 ts=4 tw=0:

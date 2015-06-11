#!/usr/bin/env bash
set -x
die_in_error() { if [ "x${?}" != "x0" ];then echo "${@}";exit 1;fi }

# 1. Create the base image template
forceimg=""
if [ ! -f /data/baseimage.tar.xz ];then
    set -e
    forceimg="y"
    lxc-create -t ${MS_OS} -n ${MS_OS} -- --packages="vim,git"\
        --release=${MS_DEB_RELEASE} --mirror=${MS_DEB_MIRROR}
    cd /var/lib/lxc/${MS_OS}/rootfs
    cp /bootstrap_scripts/* tmp
    cp /etc/apt/apt.conf.d/99{gzip,notrad,clean} etc/apt/apt.conf.d
    chroot /var/lib/lxc/${MS_OS}/rootfs /tmp/lxc-cleanup.sh
    chroot /var/lib/lxc/${MS_OS}/rootfs /tmp/makinastates-snapshot.sh
    tar cJf /data/baseimage.tar.xz .
    set +e
fi

# if the user (via a volume place a 'stage1.sh' script it will override the
# default procedure

# 2. Import the base template a the first level Layer, this image wont
#    spawn systemd by itself, but a script that builds the image.
#    This script produce the first image
mbs="${MS_IMAGE}-bootstrap"
if ! docker inspect "${mbs}" >/dev/null 2>&1;then
    forceimg="y"
fi
if [ "x${forceimg}" != "x" ];then
    dir="$(mktemp)" && rm -f "${dir}" && mkdir "${dir}" && cd "${dir}"
    cp /data/baseimage.tar.xz .
    cp -r /bootstrap_scripts .
    echo "FROM ${MS_BASE}" > Dockerfile
    if [ "x${MS_BASE}" = "xscratch" ];then
        echo "ADD baseimage.tar.xz /" >> Dockerfile
    fi
    echo "ADD bootstrap_scripts/docker_build.sh /bootstrap_scripts/docker_build.sh" >> Dockerfile
    echo "CMD /bootstrap_scripts/docker_build.sh" >> Dockerfile
    docker build -t "${mbs}" .
    die_in_error "${mbs} failed to build"
fi
# 3. Spawn a container, run systemd & install makina-states
# search first volumes we have to forward
volumes="-v /sys/fs/cgroup:/sys/fs/cgroup:ro"
volumes="${volumes} -v /usr/bin/docker:/usr/bin/docker:ro"
volumes="${volumes} -v /var/lib/docker:/var/lib/docker"
volumes="${volumes} -v /var/run/docker:/var/run/docker"
volumes="${volumes} -v /var/run/docker.sock:/var/run/docker.sock"
for i in $(find /srv/pillar /srv/mastersalt-pillar /srv/projects/*/pillar\
           -mindepth 0 -maxdepth 0 -type d 2>/dev/null);do
    volumes="${volumes} -v ${i}:${i}"
done
NAME="$(echo ${MS_IMAGE}|sed -re "s/\///g")-$(uuidgen)"
env="${env} -e MS_GIT_URL=${MS_GIT_URL} -e MS_GIT_BRANCH=${MS_GIT_BRANCH}"
env="${env} -e container=docker -e MS_DID='${NAME}' -e MS_COMMAND=${MS_COMMAND}"
env="${env} -e MS_IMAGE=${MS_IMAGE} -e MS_IMAGE_CANDIDATE=${MS_IMAGE_CANDIDATE}"
# Run the script; it's the script which is in charge to tag the image
docker run --privileged -ti --rm ${env} ${volumes} --name="${NAME}" "${mbs}"
ret=$?
docker rmi "${MS_IMAGE}-bootstrap"
if [ "x${ret}" != "x0" ];then
    false;die_in_error "${MS_IMAGE} builder script did'nt worked"
fi
# vim:set et sts=4 ts=4 tw=0:

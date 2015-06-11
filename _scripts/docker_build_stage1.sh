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

# Stage1. Create the base image template
if [ "x${MS_BASE}" = "xscratch" ];then
    if [ ! -f /data/baseimage.tar.xz ];then
        set -e
        if [ "x${MS_OS}" = "xubuntu" ];then
            red "${MS_IMAGE}: Creating baseimage for ${MS_IMAGE}"
            lxc-create -t ${MS_OS} -n ${MS_OS} -- --packages="vim,git"\
                --release=${MS_OS_RELEASE} --mirror=${MS_OS_MIRROR}
        else
            red "Other OS than ubuntu is not currently supported"
            exit 1
        fi
        cd /var/lib/lxc/${MS_OS}/rootfs
        cp /bootstrap_scripts/* tmp
        cp /etc/apt/apt.conf.d/99{gzip,notrad,clean} etc/apt/apt.conf.d
        chroot /var/lib/lxc/${MS_OS}/rootfs /tmp/lxc-cleanup.sh
        chroot /var/lib/lxc/${MS_OS}/rootfs /tmp/makinastates-snapshot.sh
        tar cJf /data/baseimage.tar.xz .
        set +e
    else
        yellow "${MS_IMAGE}: /data/baseimage.tar.xz for ${MS_IMAGE} already exists, delete it to redo"
    fi
else
    yellow "${MS_IMAGE}: ${MS_BASE} is not scratch, skipping baseimage build"
fi

# if the user (via a volume place a 'stage1.sh' script it will override the
# default procedure

# Stage2. Import the base template a the first level Layer, this image wont
#    spawn systemd by itself, but a script that builds the image.
#     script produce the first image
mbs="${MS_IMAGE}-bootstrap:latest"
mid="$(docker inspect -f "{{.Id}}" "${mbs}" 2>/dev/null)"
if [ "x${?}" != "x0" ];then
    mid=""
fi
# an image is carracterized by it's baseimage layout and the builder script
# if the md5 are matching, we can leverage docker cache.
BUILDKEY=""
BUILDKEY="${BUILDKEY}_$(md5sum /bootstrap_scripts/docker_build.sh|awk '{print $1}')"
if [ "x${MS_BASE}" = "xscratch" ];then
    BUILDKEY="${BUILDKEY}_$(md5sum /data/baseimage.tar.xz|awk '{print $1}')"
fi
# only rebuild the bootstrap image if it is useful and something changed
do_build="y"
if [ "x${mid}" != "x" ];then
    if docker inspect -f "{{.ContainerConfig.Labels.MS_IMAGE_BUILD_KEY}}" "${mbs}" | grep -q "${BUILDKEY}";then
        do_build=""
    fi
fi
if [ "x${do_build}" != "x" ];then
    dir="$(mktemp)" && rm -f "${dir}" && mkdir "${dir}" && cd "${dir}"
    echo "FROM ${MS_BASE}" > Dockerfile
    if [ "x${MS_BASE}" = "xscratch" ];then
        echo "ADD baseimage.tar.xz /" >> Dockerfile
        cp /data/baseimage.tar.xz .
    fi
    cp -rf /bootstrap_scripts .
    echo "ADD bootstrap_scripts/docker_build.sh /bootstrap_scripts/docker_build.sh" >> Dockerfile
    echo "LABEL MS_IMAGE_BUILD_KEY=\"${BUILDKEY}\"" >> Dockerfile
    echo "CMD /bootstrap_scripts/docker_build.sh" >> Dockerfile
    red "${MS_IMAGE}: Bootstraping image ${mbs} with this Dockerfile"
    cat Dockerfile
    docker build -t "${mbs}" .
    # cleanup the old bootstrap image
    if [ "x${?}" = "x0" ] && [ "x${mid}" != "x" ] ;then
        yellow "${MS_IMAGE}: Deleting old bootstrap layer: ${mid}"
        docker rmi "${mid}"
    fi
else
    yellow "${MS_IMAGE}: Bootstrap image ${mbs} already built, skipping"
fi

exit 1
die_in_error "${mbs} failed to build"

# Stage3. Spawn a container, run systemd & install makina-states
volumes="-v /sys/fs/cgroup:/sys/fs/cgroup:ro"
volumes="${volumes} -v /usr/bin/docker:/usr/bin/docker:ro"
volumes="${volumes} -v /var/lib/docker:/var/lib/docker"
volumes="${volumes} -v /var/run/docker:/var/run/docker"
volumes="${volumes} -v /var/run/docker.sock:/var/run/docker.sock"
volumes="${volumes} -v /bootstrap_scripts:/forwarded_volumes/bootstrap_scripts"
for i in $(\
    find \
         /srv/pillar \
         /srv/mastersalt-pillar \
         /srv/projects \
    -mindepth 0 -maxdepth 0 -type d 2>/dev/null);do
    volumes="${volumes} -v ${i}:/forwarded_volumes/${i}"
done
NAME="$(echo ${MS_IMAGE}|sed -re "s/\///g")-$(uuidgen)"

# Run the script; it's the script which is in charge to tag the image
docker run --net="host" \
    --privileged -ti --rm \
    -e container="docker"
    -e MS_GIT_URL="${MS_GIT_URL}" \
    -e MS_GIT_BRANCH="${MS_GIT_BRANCH}" \
    -e MS_DID="${NAME}" \
    -e MS_COMMAND="${MS_COMMAND}" \
    -e MS_IMAGE="${MS_IMAGE}" \
    -e MS_IMAGE_CANDIDATE="${MS_IMAGE_CANDIDATE}" \
    ${volumes} \
    --name="${NAME}" "${mbs}"
ret=$?
if [ "x${ret}" != "x0" ];then
    false;die_in_error "${MS_IMAGE} builder script did'nt worked"
else
    docker rmi "${mbs}"
fi
# vim:set et sts=4 ts=4 tw=0:

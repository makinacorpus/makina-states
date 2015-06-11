#!/usr/bin/env bash
RED='\e[31;01m'
PURPLE='\e[33;01m'
CYAN='\e[36;01m'
YELLOW='\e[33;01m'
GREEN='\e[32;01m'
NORMAL='\e[0m'

purple() { echo -e "${PURPLE}${@}${NORMAL}"; }
red() { echo -e "${RED}${@}${NORMAL}"; }
cyan() { echo -e "${CYAN}${@}${NORMAL}"; }
yellow() { echo -e "${YELLOW}${@}${NORMAL}"; }
green() { echo -e "${GREEN}${@}${NORMAL}"; }
die_in_error() { if [ "x${?}" != "x0" ];then red "${@}";exit 1;fi }
v_run() { green "${@}"; "${@}"; }

echo;echo
yellow "-----------------------------------------------"
yellow "-   STAGE 1  - BUIDING                        -"
yellow "-----------------------------------------------"
echo

BASEIMAGE="/docker_data/baseimage-${MS_OS}-${MS_OS_RELEASE}.tar.xz"

# Stage1. Create the base image template
if [ "x${MS_BASE}" = "x" ];then
    export MS_BASE="scratch"
fi
if [ "x${MS_BASE}" = "xscratch" ];then
    if [ ! -f "${BASEIMAGE}" ];then
        if [ "x${MS_OS}" = "xubuntu" ];then
            red "${MS_IMAGE}: Creating baseimage ${BASEIMAGE} for ${MS_IMAGE}"
            v_run lxc-create -t ${MS_OS} -n ${MS_OS} -- --packages="vim,git"\
                --release=${MS_OS_RELEASE} --mirror=${MS_OS_MIRROR}
            die_in_error "${MS_IMAGE}: lxc template failed"
        else
            red "${MS_IMAGE}: Other OS than ubuntu is not currently supported (${MS_OS})"
            exit 1
        fi
        set -e
        cd /var/lib/lxc/${MS_OS}/rootfs
        v_run rsync -a /bootstrap_scripts/ bootstrap_scripts/
        v_run cp /etc/apt/apt.conf.d/99{gzip,notrad,clean} etc/apt/apt.conf.d
        v_run chroot /var/lib/lxc/${MS_OS}/rootfs /bootstrap_scripts/lxc-cleanup.sh
        v_run chroot /var/lib/lxc/${MS_OS}/rootfs /bootstrap_scripts/makinastates-snapshot.sh
        set -e
        v_run tar cJf "${BASEIMAGE}" .
        die_in_error "${MS_IMAGE}: can't compress ${BASEIMAGE}"
    else
        green "${MS_IMAGE}: ${BASEIMAGE} for ${MS_IMAGE} already exists"
        yellow "${MS_IMAGE}: Delete it to redo"
    fi
else
    yellow "${MS_IMAGE}: ${MS_BASE} is not \"scratch\", skipping baseimage build"
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
BUILDKEY="${BUILDKEY}_$(md5sum /bootstrap_scripts/stage2.sh|awk '{print $1}')"
BUILDKEY="${BUILDKEY}_$(md5sum /bootstrap_scripts/stage3.sh|awk '{print $1}')"
if [ "x${MS_BASE}" = "xscratch" ] && [ -f "${BASEIMAGE}" ] ;then
    BUILDKEY="${BUILDKEY}_$(md5sum "${BASEIMAGE}"|awk '{print $1}')"
fi
# only rebuild the bootstrap image if it is useful and something changed
do_build="y"
if [ "x${mid}" != "x" ];then
    if docker inspect -f "{{.ContainerConfig.Labels.MS_IMAGE_BUILD_KEY}}" "${mbs}" | grep -q "${BUILDKEY}";then
        do_build=""
    fi
fi
if [ "x${do_build}" != "x" ];then
    cd /
    echo "FROM ${MS_BASE}" > Dockerfile
    if [ "x${MS_BASE}" = "xscratch" ];then
        echo "ADD ${BASEIMAGE} /" >> Dockerfile
        cp "${BASEIMAGE}" .
    fi
    cp -rf /bootstrap_scripts .
    echo "LABEL MS_IMAGE_BUILD_KEY=\"${BUILDKEY}\"" >> Dockerfile
    echo "CMD /forwarded_volumes/bootstrap_scripts/stage2.sh" >> Dockerfile
    red "${MS_IMAGE}: Bootstraping image ${mbs} with this Dockerfile"
    cat Dockerfile
    v_run docker build -t "${mbs}" .
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
purple "--------------------"
purple "- stage1 complete  -"
purple "--------------------"

# Stage2. Spawn a container, run systemd & install makina-states
for i in /srv/pillar /srv/mastersalt-pillar /srv/projects;do
    if [ ! -d ${i} ];then mkdir ${i};fi
done
NAME="$(echo ${MS_IMAGE}|sed -re "s/\///g")-$(uuidgen)"
# Run the script which is in charge to tag a candidate image after a
# sucessful build
MS_IMAGE_CANDIDATE="${MS_IMAGE}:candidate"
v_run docker run \
 -e container="docker" \
 -e MS_BASE="${MS_BASE}" \
 -e MS_COMMAND="${MS_COMMAND}" \
 -e MS_DID="${NAME}" \
 -e MS_GIT_BRANCH="${MS_GIT_BRANCH}" \
 -e MS_GIT_URL="${MS_GIT_URL}" \
 -e MS_IMAGE_CANDIDATE="${MS_IMAGE_CANDIDATE}" \
 -e MS_IMAGE="${MS_IMAGE}" \
 -e MS_OS_MIRROR="${MS_OS_MIRROR}" \
 -e MS_OS="${MS_OS}" \
 -e MS_OS_RELEASE="${MS_OS_RELEASE}" \
 -e MS_STAGE0_TAG="${MS_STAGE0_TAG}" \
 -v /docker_data:/docker_data \
 -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
 -v /usr/bin/docker:/usr/bin/docker:ro \
 -v /var/lib/docker:/var/lib/docker \
 -v /var/run/docker:/var/run/docker \
 -v /var/run/docker.sock:/var/run/docker.sock \
 -v /bootstrap_scripts:/forwarded_volumes/bootstrap_scripts \
 -v /srv/pillar:/forwarded_volumes/srv/pillar \
 -v /srv/mastersalt-pillar:/forwarded_volumes/srv/mastersalt-pillar \
 -v /srv/projects:/forwarded_volumes/srv/projects \
 --net="host" --privileged -ti --rm --name="${NAME}" "${mbs}"
ret=${?}
docker rmi "${mbs}"
exit ${ret}
# vim:set et sts=4 ts=4 tw=0:

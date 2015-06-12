#!/usr/bin/env bash
# THIS SCRIPT CAN BE OVERRIDEN IN ANY MAKINA-STATES BASED IMAGES
# REMOVE/EDIT THE ROLLOWING MARKER TO UNINDICATE THAT THIS IS A DEFAULT SCRIPT
# makina-states-default-stage-file
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
warn_in_error() { if [ "x${?}" != "x0" ];then yellow "WARNING: ${@}";exit 1;fi }
v_run() { green "${@}"; "${@}"; }
v_die_run() { v_run "${@}"; die_in_error "command ${@} failed"; }

MS_BASEIMAGE_DIR="${MS_BASEIMAGE_DIR:-"/docker/data"}"
MS_BASEIMAGE_PATH="${MS_BASEIMAGE_DIR}/${MS_BASEIMAGE}"
MS_BASEIMAGE_ADD="data/${MS_BASEIMAGE}"

echo;echo
yellow "-----------------------------------------------"
yellow "-   STAGE 1  - BUIDING                        -"
yellow "-----------------------------------------------"
echo

# Stage1. Create the base image template
if [ "x${MS_BASE}" = "x" ];then
    export MS_BASE="scratch"
fi
if [ "x${MS_BASE}" = "xscratch" ];then
    if [ ! -f "${MS_BASEIMAGE_PATH}" ];then
        if [ "x${MS_OS}" = "xubuntu" ];then
            red "${MS_IMAGE}: Creating baseimage ${MS_BASEIMAGE} for ${MS_IMAGE}"
            v_run lxc-create -t ${MS_OS} -n ${MS_OS} -- --packages="vim,git"\
                --release=${MS_OS_RELEASE} --mirror=${MS_OS_MIRROR}
            die_in_error "${MS_IMAGE}: lxc template failed"
        else
            red "${MS_IMAGE}: Other OS than ubuntu is not currently supported (${MS_OS})"
            exit 1
        fi
        cd /var/lib/lxc/${MS_OS}/rootfs
        if [ ! -d injected_volumes];then mkdir injected_volumes;fi
        v_die_run rsync -aA /injected_volumes/bootstrap_scripts/ injected_volumes/bootstrap_scripts/
        v_die_run cp /etc/apt/apt.conf.d/99{gzip,notrad,clean} etc/apt/apt.conf.d
        v_die_run chroot /var/lib/lxc/${MS_OS}/rootfs /injected_volumes/bootstrap_scripts/lxc-cleanup.sh
        v_die_run chroot /var/lib/lxc/${MS_OS}/rootfs /injected_volumes/bootstrap_scripts/makinastates-snapshot.sh
        v_die_run tar cJf "${MS_BASEIMAGE_PATH}" .
        die_in_error "${MS_IMAGE}: can't compress ${MS_BASEIMAGE}"
    else
        green "${MS_IMAGE}: ${MS_BASEIMAGE} for ${MS_IMAGE} already exists"
        yellow "${MS_IMAGE}: Delete it to redo"
    fi
else
    green "${MS_IMAGE}: ${MS_BASE} is not \"scratch\", skipping baseimage build"
fi

# if the user (via a volume place a 'stage1.sh' script it will override the
# default procedure

# Stage2. Import the base template a the first level Layer, this image wont
#    spawn systemd by itself, but a script that builds the image.
#     script produce the first image
stage1_tag="${MS_IMAGE}-stage1:latest"
mid="$(docker inspect -f "{{.Id}}" "${stage1_tag}" 2>/dev/null)"
if [ "x${?}" != "x0" ];then
    mid=""
fi
# an image is carracterized by it's baseimage layout and the builder script
# if the md5 are matching, we can leverage docker cache.
echo "FROM ${MS_BASE}" > /docker/Dockerfile
echo "CMD /injected_volumes/bootstrap_scripts/stage2.sh" >> /docker/Dockerfile
if [ "x${MS_BASE}" = "xscratch" ];then
    echo "ADD ${MS_BASEIMAGE_ADD} /" >> /docker/Dockerfile
fi
echo "RUN apt-get update && apt-get install -y --force-yes acl rsync git" >> /docker/Dockerfile
BUILDKEY=""
BUILDKEY="${BUILDKEY}_$(md5sum /bootstrap_scripts/stage2.sh|awk '{print $1}')"
BUILDKEY="${BUILDKEY}_$(md5sum /bootstrap_scripts/stage3.sh|awk '{print $1}')"
BUILDKEY="${BUILDKEY}_$(md5sum /docker/Dockerfile|awk '{print $1}')"
if [ "x${MS_BASE}" = "xscratch" ] && [ -f "${MS_BASEIMAGE_PATH}" ] ;then
    BUILDKEY="${BUILDKEY}_$(md5sum "${MS_BASEIMAGE_PATH}"|awk '{print $1}')"
fi
# only rebuild the stage1 image if it is useful and something changed
do_build="y"
if [ "x${mid}" != "x" ];then
    if docker inspect -f "{{.ContainerConfig.Labels.MS_IMAGE_BUILD_KEY}}" "${stage1_tag}" | grep -q "${BUILDKEY}";then
        do_build=""
    fi
fi
if [ "x${do_build}" != "x" ];then
    echo "LABEL MS_IMAGE_BUILD_KEY=\"${BUILDKEY}\"" >> /docker/Dockerfile
    cyan "------------"
    cyan "${MS_IMAGE}: Bootstraping image ${stage1_tag} with this Dockerfile"
    cyan "------------"
    cat /docker/Dockerfile
    cyan "------------"
    v_run docker build -t "${stage1_tag}" /docker
    die_in_error "${stage1_tag} failed to build stage1 image"
    # cleanup the old stage1 image
    if [ "x${?}" = "x0" ] && [ "x${mid}" != "x" ] ;then
        yellow "${MS_IMAGE}: Deleting old stage1 layer: ${mid}"
        docker rmi "${mid}"
        warn_in_error "${MS_IMAGE}: stage1 old: ${mid} was not deleted"
    fi
else
    yellow "${MS_IMAGE}: stage1 image ${stage1_tag} already built, skipping"
fi

echo
purple "--------------------"
purple "- stage1 complete  -"
purple "--------------------"
echo
# Stage2. Spawn a container, run systemd & install makina-states
for i in /srv/pillar /srv/mastersalt-pillar /srv/projects;do
    if [ ! -d ${i} ];then mkdir ${i};fi
done
NAME="$(echo ${MS_IMAGE}|sed -re "s/\///g")-stage1-$(uuidgen)"
# Run the script which is in charge to tag a candidate image after a
# sucessful build
MS_IMAGE_CANDIDATE="${MS_IMAGE}:candidate"
#-v /makina-states.git:/makina-states.git \
#-v /docker/data:/docker/data \
#-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
#-v /usr/bin/docker:/usr/bin/docker:ro \
#-v /var/lib/docker:/var/lib/docker \
#-v /var/run/docker:/var/run/docker \
#-v /var/run/docker.sock:/var/run/docker.sock \
#-v /bootstrap_scripts:/injected_volumes/bootstrap_scripts \
#-v /srv/pillar:/injected_volumes/srv/pillar \
#-v /srv/mastersalt-pillar:/injected_volumes/srv/mastersalt-pillar \
#-v /srv/projects:/injected_volumes/srv/projects \
v_run docker run \
 -e container="docker" \
 -e MS_BASE="${MS_BASE}" \
 -e MS_COMMAND="${MS_COMMAND}" \
 -e MS_STAGE1_NAME="${MS_STAGE1_NAME}" \
 -e MS_STAGE2_NAME="${MS_STAGE2_NAME}" \
 -e MS_GIT_BRANCH="${MS_GIT_BRANCH}" \
 -e MS_GIT_URL="${MS_GIT_URL}" \
 -e MS_IMAGE_CANDIDATE="${MS_IMAGE_CANDIDATE}" \
 -e MS_IMAGE="${MS_IMAGE}" \
 -e MS_OS_MIRROR="${MS_OS_MIRROR}" \
 -e MS_OS="${MS_OS}" \
 -e MS_OS_RELEASE="${MS_OS_RELEASE}" \
 -e MS_STAGE0_TAG="${MS_STAGE0_TAG}" \
 --volume-from="${MS_STAGE1_NAME}" \
 --net="host" --privileged -ti --rm --name="${NAME}" ${stage1_tag} ls /injected_volumes/bootstrap_scripts
# --net="host" --privileged -ti --rm --name="${NAME}" "${stage1_tag}"
/bin/false
ret=${?}
# only delete cache1 on sucesssul build to speed up cache rebuilds
if [ "x${ret}" = "x0" ];then docker rmi "${stage1_tag}";fi
exit ${ret}
# vim:set et sts=4 ts=4 tw=0:

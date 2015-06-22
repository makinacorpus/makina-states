#!/usr/bin/env bash
# THIS SCRIPT CAN BE OVERRIDEN IN ANY MAKINA-STATES BASED IMAGES
# Copy/Edit it inside the image_rootfs directory inside you image data directory:
# ${MS_DATA_DIR}/${MS_IMAGE}
# EG:
#  cp stage1.sh /srv/foo/makina-states/data/mycompany/mydocker/image_rootfs/bootstrap_scripts/stage1.sh
#  $ED /srv/foo/makina-states/data/mycompany/mydocker/image_rootfs/bootstrap_scripts/stage1.sh

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
warn_in_error() { if [ "x${?}" != "x0" ];then yellow "WARNING: ${@}";fi }
v_run() { green "${@}"; "${@}"; }
v_die_run() { v_run "${@}"; die_in_error "command ${@} failed"; }
a_d() { echo "${@}" >> "${dockerfile}"; }

MS_BASEIMAGE_DIR="${MS_BASEIMAGE_DIR:-"/docker/data"}"
MS_BASEIMAGE_PATH="${MS_BASEIMAGE_DIR}/${MS_BASEIMAGE}"
MS_BASEIMAGE_ADD="data/${MS_BASEIMAGE}"
rdockerfile="injected_volumes/bootstrap_scripts/Dockerfile.stage1"
dockerfile="/docker/${rdockerfile}"

echo;echo
yellow "-----------------------------------------------"
yellow "-   STAGE 1  - BUIDING                        -"
yellow "-----------------------------------------------"
echo

if [ "x${MS_BASE}" = "x" ];then
    export MS_BASE="scratch"
fi

# Stage1. Create the base image template from an lxc container if supported
if [ "x${MS_BASE}" = "xscratch" ];then
    if [ ! -f "${MS_BASEIMAGE_PATH}" ];then
        if [ "x${MS_OS}" = "xubuntu" ];then
            red "${MS_IMAGE}: Creating baseimage ${MS_BASEIMAGE} for ${MS_IMAGE}"
            v_run lxc-create -t ${MS_OS} -n ${MS_OS} -- --packages="vim,git,rsync,acl,ca-certificates"\
                --release=${MS_OS_RELEASE} --mirror=${MS_OS_MIRROR}
            die_in_error "${MS_IMAGE}: lxc template failed"
        else
            red "${MS_IMAGE}: Other OS than ubuntu is not currently supported (${MS_OS})"
            exit 1
        fi
        cd /var/lib/lxc/${MS_OS}/rootfs
        if [ ! -d docker/injected_volumes ];then mkdir -p docker/injected_volumes;fi
        v_die_run tar cJf "${MS_BASEIMAGE_PATH}" .
        die_in_error "${MS_IMAGE}: can't compress ${MS_BASEIMAGE}"
    else
        green "${MS_IMAGE}: ${MS_BASEIMAGE} for ${MS_IMAGE} already exists"
        yellow "${MS_IMAGE}: Delete it to redo"
    fi
else
    green "${MS_IMAGE}: ${MS_BASE} is not \"scratch\", skipping baseimage build"
fi

# Stage2. Import the base template a the first level Layer, this image won' t
#  spawn systemd by itself,
#  It is the command (build script aka stage3.sh) which
#    - will lanch init (certainly systemd)
#    - launch the projects building & image finalization
stage1_tag="${MS_IMAGE}-stage1:latest"
mid="$(docker inspect -f "{{.Id}}" "${stage1_tag}" 2>/dev/null)"
if [ "x${?}" != "x0" ];then
    mid=""
fi
# An image is carracterized by
#   - it's baseimage layout
#   - it's builder script & stage3 builder
# if the md5 are matching, we can leverage docker cache.
echo "FROM ${MS_BASE}" > "${dockerfile}"
add=""
if [ "x${MS_BASE}" = "xscratch" ];then add="${add} ${MS_BASEIMAGE_ADD}";fi
# base survival apt configuration
if [ "x${MS_OS}" = "xubuntu" ];then
    tar cvf  /docker/ubuntufiles.tar -C /docker/makina-states/docker/ubuntu .
    die_in_error "${MS_IMAGE}: cant tar source.list for ubuntu"
    tar rvf /docker/ubuntufiles.tar -C /docker/makina-states/files\
        etc/apt/preferences.d/00_proposed.pref\
        etc/apt/preferences.d/99_systemd.pref\
        etc/apt/apt.conf.d/99gzip\
        etc/apt/apt.conf.d/99notrad\
        etc/systemd/system/lxc-setup.service\
        etc/apt/apt.conf.d/99clean\
        usr/bin/ms-lxc-setup.sh\
        sbin/lxc-cleanup.sh
    die_in_error "${MS_IMAGE}: cant tar aptconf"
    add="${add} ubuntufiles.tar"
fi
if [ "x${add}" != "x" ];then a_d "ADD ${add} /";fi
# install core pkgs & be sure to have up to date systemd on ubuntu systemd enabled
a_d "RUN \
    echo DOCKERFILE_ID=3\\
    && if which apt-get >/dev/null 2>&1;then\\
      sed -i -re\
          \"s/Pin: .*/Pin: release a=\$(lsb_release -sc)-proposed/g\"\
          /etc/apt/preferences.d/*\\
      && sed -i -re\
          \"s/__ubunturelease__/\$(lsb_release -sc)/g\"\
          /etc/apt/sources.list\\
      && apt-get update\\
      && apt-get install -y --force-yes\\
          acl rsync git e2fsprogs ca-certificates\\
      && if dpkg -l |grep systemd|awk '{print \$1 \$2}'|egrep -q '^iisystemd';\\
          then apt-get install -y --force-yes\\
          systemd libpam-systemd systemd-sysv libsystemd0;fi;\\
   fi\\
   && /docker/injected_volumes/bootstrap_scripts/lxc-cleanup.sh\\
   && /docker/injected_volumes/bootstrap_scripts/makinastates-snapshot.sh\\
   && sed -i -re \"s/PrivDropToUser.*/PrivDropToUser root/g\"\
       /etc/rsyslog.conf\\
   && sed -i -re \"s/PrivDropToGroup*/PrivDropToGroup root/g\"\
       /etc/rsyslog.conf\\
   && chmod 755 /sbin/lxc-cleanup.sh /usr/bin/ms-lxc-setup.sh\\
   && if test -e /lib/systemd/systemd;then\\
          if ! test -e /etc/systemd/system/network-online.target.wants;then\\
            mkdir -pv /etc/systemd/system/network-online.target.wants;\\
          fi;\\
          ln -sf /etc/systemd/system/lxc-setup.service\\
          /etc/systemd/system/network-online.target.wants/lxc-setup.service;\\
      fi"
a_d "CMD /docker/injected_volumes/bootstrap_scripts/stage2.sh"
BUILDKEY=""
BUILDKEY="${BUILDKEY}_$(md5sum\
    /docker/injected_volumes/bootstrap_scripts/stage2.sh|awk '{print $1}')"
BUILDKEY="${BUILDKEY}_$(md5sum\
    /docker/injected_volumes/bootstrap_scripts/stage3.sh|awk '{print $1}')"
BUILDKEY="${BUILDKEY}_$(md5sum ${dockerfile}|awk '{print $1}')"
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
    a_d "LABEL MS_IMAGE_BUILD_KEY=\"${BUILDKEY}\""
    cyan "------------------------------------------------------------------------------"
    cyan "${MS_IMAGE}:"
    echo "     Bootstraping image: $(green ${stage1_tag})"
    echo "     with this Dockerfile: $(green /bootstrap_scripts/Dockerfile.stage1)"
    cyan "-------------------------------------------------------------------------------"
    cat "${dockerfile}"
    cyan "-------------------------------------------------------------------------------"
    v_run docker build -t "${stage1_tag}" -f "${dockerfile}" /docker
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
# Run the script which is in charge to tag a candidate image after a
# sucessful build
v_run docker run \
 -e container="docker" \
 -e MS_BASE="${MS_BASE}" \
 -e MS_BASEIMAGE="${MS_BASEIMAGE}" \
 -e MS_COMMAND="${MS_COMMAND}" \
 -e MS_GIT_BRANCH="${MS_GIT_BRANCH}" \
 -e MS_GIT_URL="${MS_GIT_URL}" \
 -e MS_IMAGE_CANDIDATE="${MS_IMAGE_CANDIDATE}" \
 -e MS_IMAGE="${MS_IMAGE}" \
 -e MS_OS_MIRROR="${MS_OS_MIRROR}" \
 -e MS_OS="${MS_OS}" \
 -e MS_OS_RELEASE="${MS_OS_RELEASE}" \
 -e MS_STAGE0_TAG="${MS_STAGE0_TAG}" \
 -e MS_STAGE1_NAME="${MS_STAGE1_NAME}" \
 -e MS_STAGE2_NAME="${MS_STAGE2_NAME}" \
 -e MS_DO_SNAPSHOT="${MS_DO_SNAPSHOT}" \
 -e MS_MAKINASTATES_BUILD_DISABLED="${MS_MAKINASTATES_BUILD_DISABLED}" \
 --volumes-from="${MS_STAGE1_NAME}" \
 ${MS_DOCKER_ARGS} \
 --privileged -ti --rm --name="${MS_STAGE2_NAME}"\
 ${stage1_tag}
ret=${?}
# only delete cache1 on sucesssul build to speed up cache rebuilds
if [ "x${ret}" = "x0" ];then docker rmi "${stage1_tag}";fi
exit ${ret}
# vim:set et sts=4 ts=4 tw=0:

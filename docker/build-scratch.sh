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
warn_in_error() { if [ "x${?}" != "x0" ];then yellow "WARNING: ${@}";fi }
v_run() { green "${@}"; "${@}"; }
v_die_run() { v_run "${@}"; die_in_error "command ${@} failed"; }
a_d() { echo "${@}" >> "${dockerfile}"; }

W="${MS_TARGET:-$(cd $(dirname ${0}) && pwd)}"
MS_OS="${MS_OS:-ubuntu}"
MS_OS_RELEASE="${MS_OS_RELEASE:-vivid}"
MS_BASEIMAGE="baseimage-${MS_OS}-${MS_OS_RELEASE}.tar.xz"
MS_OS_MIRROR="${MS_OS_MIRROR:-http://mirror.ovh.net/ftp.ubuntu.com/}"
MS_OS_IMAGE="${MS_OS_IMAGE:-makinacorpus/makina-states:latest}"
MS_BASEIMAGE_DIR="${MS_BASEIMAGE_DIR:-"${W}"}"
MS_BASEIMAGE_PATH="${MS_BASEIMAGE_DIR}/${MS_BASEIMAGE}"
rdockerfile="Dockerfile"
dockerfile="${W}/${rdockerfile}"

echo;echo
yellow "-----------------------------------------------"
yellow "-   STAGE 1  - BUIDING                        -"
yellow "-----------------------------------------------"
echo

# Stage1. Create the base image template from an lxc container if supported
if [ ! -f "${MS_BASEIMAGE_PATH}" ];then
    if [ "x${MS_OS}" = "xubuntu" ];then
        red "${MS_IMAGE}: Creating baseimage ${MS_BASEIMAGE} for ${MS_IMAGE}"
        v_run lxc-create -t ${MS_OS} -n ms-${MS_OS}-${MS_OS_RELEASE} \
            -- --packages="vim,git,rsync,acl,ca-certificates,socat,tcpdump,netcat"\
            --release=${MS_OS_RELEASE} --mirror=${MS_OS_MIRROR}
        die_in_error "${MS_IMAGE}: lxc template failed"
    else
        red "${MS_IMAGE}: Other OS than ubuntu is not currently supported (${MS_OS})"
        exit 1
    fi
    cd /var/lib/lxc/${MS_OS}/rootfs
    # if [ ! -d docker/injected_volumes ];then mkdir -p docker/injected_volumes;fi
    v_die_run tar cJf "${MS_BASEIMAGE_PATH}.tmp" .
    die_in_error "${MS_IMAGE}: can't compress ${MS_BASEIMAGE}.tmp"
    mv -f "${MS_BASEIMAGE_PATH}.tmp" "${MS_BASEIMAGE_PATH}"
    die_in_error "${MS_IMAGE}: can't move tarball to ${MS_BASEIMAGE}"
else
    green "${MS_IMAGE}: ${MS_BASEIMAGE} for ${MS_IMAGE} already exists"
    yellow "${MS_IMAGE}: Delete it to redo"
fi
mid="$(docker inspect -f "{{.Id}}" "${MS_IMAGE}" 2>/dev/null)"
if [ "x${?}" != "x0" ];then
    mid=""
fi
# An image is carracterized by
#   - it's baseimage layout
#   - it's builder script & stage3 builder
# if the md5 are matching, we can leverage docker cache.
echo "FROM scratch" > "${dockerfile}"
a_d "ADD ${MS_BASEIMAGE} /"
# base survival apt configuration
if [ "x${MS_OS}" = "xubuntu" ];then
    tar cvf $W/ubuntufiles.tar -C ubuntu .
    die_in_error "${MS_IMAGE}: cant tar source.list for ubuntu"
    tar rvf $W/ubuntufiles.tar -C ../files\
        etc/apt/preferences.d/00_proposed.pref\
        etc/apt/preferences.d/99_systemd.pref\
        etc/apt/apt.conf.d/99gzip\
        etc/apt/apt.conf.d/99notrad\
        etc/systemd/system/lxc-setup.service\
        etc/apt/apt.conf.d/99clean\
        usr/bin/ms-lxc-setup.sh\
        sbin/lxc-cleanup.sh\
        sbin/makinastates-snapshot.sh
    die_in_error "${MS_IMAGE}: cant tar aptconf"
    a_d "ADD ubuntufiles.tar /"
fi
# files layered should be added only after to conserve
# unix permissions of containers, as makina-states repo does not
# have them setted yet.
# Additionaly, do not add directly the tarfile as permissions would
# then also be messed inside the container, and we then only copy the files
# to their final destinations afterwards
#
# One symptom of broken permissions is systemd+dbus not starting up correctly
# In case of problems, check /etc permissions !
#
# install core pkgs & be sure to have up to date systemd on ubuntu systemd enabled
a_d "RUN \\
    echo DOCKERFILE_ID=4\\
    && set -x\\
    && cd inject && cp -rf * / && cd / && rm -rf /inject\\
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
          systemd dbus libpam-systemd systemd-sysv libsystemd0;fi;\\
   fi\\
   && chmod 755 /sbin/lxc-cleanup.sh /usr/bin/ms-lxc-setup.sh\
                /sbin/makinastates-snapshot.sh\\
   && sleep 0.4\\
   && /sbin/lxc-cleanup.sh\\
   && sed -i -re \"s/PrivDropToUser.*/PrivDropToUser root/g\"\
       /etc/rsyslog.conf\\
   && sed -i -re \"s/PrivDropToGroup*/PrivDropToGroup root/g\"\
       /etc/rsyslog.conf\\
   && if test -e /lib/systemd/systemd;then\\
          if ! test -e /etc/systemd/system/network-online.target.wants;then\\
            mkdir -pv /etc/systemd/system/network-online.target.wants;\\
          fi;\\
          ln -sf /etc/systemd/system/lxc-setup.service\\
          /etc/systemd/system/network-online.target.wants/lxc-setup.service;\\
      fi\\
   && /sbin/makinastates-snapshot.sh
   "
BUILDKEY=""
BUILDKEY="${BUILDKEY}_$(md5sum ${dockerfile}|awk '{print $1}')"
if [ "x${MS_BASE}" = "xscratch" ] && [ -f "${MS_BASEIMAGE_PATH}" ] ;then
    BUILDKEY="${BUILDKEY}_$(md5sum "${MS_BASEIMAGE_PATH}"|awk '{print $1}')"
fi
# only rebuild the stage1 image if it is useful and something changed
do_build="y"
if [ "x${mid}" != "x" ];then
    if docker inspect -f "{{.ContainerConfig.Labels.MS_IMAGE_BUILD_KEY}}" "${MS_IMAGE}" | grep -q "${BUILDKEY}";then
        do_build=""
    fi
fi
if [ "x${do_build}" != "x" ];then
    a_d "LABEL MS_IMAGE_BUILD_KEY=\"${BUILDKEY}\""
    cyan "------------------------------------------------------------------------------"
    echo "     Bootstraping image: $(green ${MS_IMAGE})"
    cyan "-------------------------------------------------------------------------------"
    cat "${dockerfile}"
    cyan "-------------------------------------------------------------------------------"
    v_run docker build -t "${MS_IMAGE}" -f "${dockerfile}" .
    die_in_error "${MS_IMAGE} failed to build stage1 image"
    # cleanup the old stage1 image
    if [ "x${?}" = "x0" ] && [ "x${mid}" != "x" ] ;then
        yellow "${MS_IMAGE}: Deleting old stage1 layer: ${mid}"
        docker rmi "${mid}"
        warn_in_error "${MS_IMAGE}: stage1 old: ${mid} was not deleted"
    fi
else
    yellow "${MS_IMAGE}: stage1 image ${MS_IMAGE} already built, skipping"
fi
echo
purple "--------------------"
purple "- stage1 complete  -"
purple "--------------------"
echo
exit ${ret}
# vim:set et sts=4 ts=4 tw=0:

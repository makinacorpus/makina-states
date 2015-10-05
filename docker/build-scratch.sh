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

W="$(cd "$(dirname ${0})" && pwd)"
MS_GIT="https://github.com/makinacorpus/makina-states.git"
MS_BRANCH="${MS_BRANCH:-stable}"
MS_ROOT="$(cd "${W}/.." && pwd)"
MS_OS="${MS_OS:-ubuntu}"
MS_CHANGESET="${MS_CHANGESET:-$(cd "${MS_ROOT}" && git log "${MS_BRANCH}" -n1 HEAD|head -n 1|awk '{print $2}')}"
MS_OS_RELEASE="${MS_OS_RELEASE:-vivid}"
MS_BASEIMAGE="baseimage-${MS_OS}-${MS_OS_RELEASE}.tar.xz"
MS_OS_MIRROR="${MS_OS_MIRROR:-http://mirror.ovh.net/ftp.ubuntu.com/}"
MS_STAGE0_IMAGE="${MS_IMAGE:-makinacorpus/makina-states-${MS_OS}-${MS_OS_RELEASE}-stage0}"
MS_IMAGE="${MS_IMAGE:-makinacorpus/makina-states-${MS_OS}-${MS_OS_RELEASE}-${MS_BRANCH}}"
MS_NODETYPE="${MS_NODETYPE:-dockercontainer}"
MS_BASEIMAGE_DIR="${MS_BASEIMAGE_DIR:-"${W}"}"
MS_BASEIMAGE_PATH="${MS_BASEIMAGE_DIR}/${MS_BASEIMAGE}"
MS_BOOTSTRAP_ARGS="${MS_BOOTSTRAP_ARGS:-"-C -n ${MS_NODETYPE} -b changeset:${MS_CHANGESET} --local-mastersalt-mode masterless --local-salt-mode masterless -MM"}"

MS_DOCKERF_S0="${W}/Dockerfile.${MS_OS}-${MS_OS_RELEASE}-${MS_CHANGESET}.stage0"
MS_DOCKERF_S1="${W}/Dockerfile.${MS_OS}-${MS_OS_RELEASE}-${MS_CHANGESET}.stage1"

function render_dockerfile() {
    template="${1}"
    dest="${2:-Dockerfile}"
    sed \
       -re "s/__MS_GIT__/${MS_GIT//\//\\\/}/g" \
        -e "s/__MS_STAGE0_IMAGE__/${MS_STAGE0_IMAGE//\//\\\/}/g" \
        -e "s/__MS_BASEIMAGE__/${MS_BASEIMAGE//\//\\\/}/g" \
        -e "s/__MS_BOOTSTRAP_ARGS__/${MS_BOOTSTRAP_ARGS//\//\\\/}/g" \
        -e "s/__MS_CHANGESET__/${MS_CHANGESET//\//\\\/}/g" \
      "${template}" > "${dest}"
}

function build_stage0() {
    dockerfile="${MS_DOCKERF_S0}"
    cyan "------------------------------------------------------------------------------"
    echo "    Constructing the baseimage for docker $(green ${MS_STAGE0_IMAGE}) rootfs"
    cyan "-------------------------------------------------------------------------------"
    if [ ! -f "${MS_BASEIMAGE_PATH}" ];then
        if [ ! -e "/var/lib/lxc/ms-${MS_OS}-${MS_OS_RELEASE}/rootfs" ];then
            if [ "x${MS_OS}" = "xubuntu" ];then
                red "${MS_STAGE0_IMAGE}: Creating baseimage ${MS_BASEIMAGE} for ${MS_STAGE0_IMAGE}"
                v_run lxc-create -t ${MS_OS} -n ms-${MS_OS}-${MS_OS_RELEASE} \
                    -- --packages="vim-tiny,git,rsync,acl,ca-certificates,socat,tcpdump,netcat"\
                    --release=${MS_OS_RELEASE} --mirror=${MS_OS_MIRROR}
                die_in_error "${MS_STAGE0_IMAGE}: lxc template failed"
            else
                red "${MS_STAGE0_IMAGE}: Other OS than ubuntu is not currently supported (${MS_OS})"
                exit 1
            fi
        else
            yellow "${MS_STAGE0_IMAGE}: container already exists"
        fi
        v_die_run cd "/var/lib/lxc/ms-${MS_OS}-${MS_OS_RELEASE}/rootfs"
        # if [ ! -d docker/injected_volumes ];then mkdir -p docker/injected_volumes;fi
        v_die_run tar cJf "${MS_BASEIMAGE_PATH}.tmp" .
        die_in_error "${MS_STAGE0_IMAGE}: can't compress ${MS_BASEIMAGE}.tmp"
        mv -f "${MS_BASEIMAGE_PATH}.tmp" "${MS_BASEIMAGE_PATH}"
        die_in_error "${MS_STAGE0_IMAGE}: can't move tarball to ${MS_BASEIMAGE}"
    else
        yellow "${MS_STAGE0_IMAGE}: ${MS_BASEIMAGE} already exists, delete it to redo"
    fi
    mid="$(docker inspect -f "{{.Id}}" "${MS_STAGE0_IMAGE}" 2>/dev/null)"
    if [ "x${?}" != "x0" ];then
        mid=""
    fi
    # An image is carracterized by
    #   - it's baseimage layout
    #   - the dockerfile
    #   - the os specific files
    # if the md5 are matching, we can leverage docker cache.
    cd "${W}"
    render_dockerfile "$W/Dockerfile.stage0.in" "${dockerfile}"
    BUILDKEY=""
    BUILDKEY="${BUILDKEY}_$(md5sum ${dockerfile}|awk '{print $1}')"
    if [ -f "${MS_BASEIMAGE_PATH}" ] ;then
        BUILDKEY="${BUILDKEY}_$(md5sum "${MS_BASEIMAGE_PATH}"|awk '{print $1}')"
    fi
    # only rebuild the image if it is useful and something changed
    do_build="y"
    if [ "x${mid}" != "x" ];then
        if docker inspect -f "{{.ContainerConfig.Labels.MS_STAGE0_IMAGE_BUILD_KEY}}" "${MS_STAGE0_IMAGE}" | grep -q "${BUILDKEY}";then
            do_build=""
        fi
    fi
    if [ "x${do_build}" != "x" ];then
        touch "$W/.osfiles"
        tar cf "$W/osfiles.tar" -C "${W}" .osfiles
        rm -f "$W/.osfiles"
        # base survival apt configuration
        if [ "x${MS_OS}" = "xubuntu" ];then
            yellow "${MS_STAGE0_IMAGE}: Adding base files to stage0"
            tar rf "$W/osfiles.tar" -C "${W}/ubuntu" .
            die_in_error "${MS_STAGE0_IMAGE}: cant tar source.list for ubuntu"
            tar rf "$W/osfiles.tar" -C "${MS_ROOT}/files"\
                etc/apt/preferences.d/00_proposed.pref\
                etc/apt/preferences.d/99_systemd.pref\
                etc/apt/apt.conf.d/99gzip\
                etc/apt/apt.conf.d/99notrad\
                etc/systemd/system/lxc-setup.service\
                etc/apt/apt.conf.d/99clean\
                usr/bin/ms-lxc-setup.sh\
                sbin/lxc-cleanup.sh\
                sbin/makinastates-snapshot.sh
            die_in_error "${MS_STAGE0_IMAGE}: cant tar aptconf"
        fi
        a_d "LABEL MS_STAGE0_IMAGE_BUILD_KEY=\"${BUILDKEY}\""
        cyan "------------------------------------------------------------------------------"
        echo "     Bootstraping image: $(green ${MS_STAGE0_IMAGE})"
        cyan "-------------------------------------------------------------------------------"
        cat "${dockerfile}"
        cyan "-------------------------------------------------------------------------------"
        ( cd "${MS_ROOT}" && v_run docker build --rm -t "${MS_STAGE0_IMAGE}" -f "${dockerfile}" . )
        die_in_error "${MS_STAGE0_IMAGE} failed to build stage0 image"
        # cleanup the old stage1 image
        if [ "x${?}" = "x0" ] && [ "x${mid}" != "x" ] ;then
            yellow "${MS_STAGE0_IMAGE}: Deleting old stage0 layer: ${mid}"
            docker rmi "${mid}"
            warn_in_error "${MS_STAGE0_IMAGE}: old stage0 old: ${mid} was not deleted"
        fi
    else
        yellow "${MS_STAGE0_IMAGE}: stage0 image ${MS_STAGE0_IMAGE} already built, skipping"
    fi
    purple "--------------------"
    purple "- stage0 complete  -"
    purple "--------------------"
    echo
}

function build_image() {
    dockerfile="${MS_DOCKERF_S1}"
    # install a basic makina-states docker compatible environment
    # inspired from https://github.com/tianon/docker-brew-ubuntu-core/blob/master/vivid/Dockerfile
    tar cf "$W/makina-states.tar" --xform="s|^|/srv/salt/makina-states/|g" -C "${MS_ROOT}" .git _scripts\
      && tar rf "$W/makina-states.tar" --xform="s|^|/srv/mastersalt/makina-states/|g" -C "${MS_ROOT}" .git _scripts\
      && xz -fk9 "$W/makina-states.tar"
    die_in_error "Cant compress makina-states"
    cd "${W}"
    render_dockerfile "$W/Dockerfile.stage1.in" ${dockerfile}
    mid="$(docker inspect -f "{{.Id}}" "${MS_IMAGE}" 2>/dev/null)"
    BUILDKEY=""
    BUILDKEY="${BUILDKEY}_$(md5sum ${dockerfile}|awk '{print $1}')"
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
        #( cd "${MS_ROOT}" &&  v_run docker build -t "${MS_IMAGE}" -f "${dockerfile}" . ) || exit 1
        ( cd "${MS_ROOT}" &&  v_run docker build --rm -t "${MS_IMAGE}" -f "${dockerfile}" . )
        die_in_error "${MS_IMAGE} failed to build image"
        # cleanup the old stage1 image
        if [ "x${?}" = "x0" ] && [ "x${mid}" != "x" ] ;then
            yellow "${MS_IMAGE}: Deleting old layer: ${mid}"
            docker rmi "${mid}"
            warn_in_error "${MS_IMAGE}: old ${mid} was not deleted"
        fi
    else
        yellow "${MS_IMAGE}: image ${MS_IMAGE} already built, skipping"
    fi
    echo
    purple "------------------------"
    purple "- baseimage complete   -"
    purple "------------------------"
    echo
}

function docker_cleanup() {
    $(dirname $0)/cleanup.sh
}

function full_cleanup() {
    for i in\
     "${W}/Dockerfile.${MS_OS}-${MS_OS_RELEASE}-"*".stage0"\
     "${W}/Dockerfile.${MS_OS}-${MS_OS_RELEASE}-"*".stage1"\
    ;do
        if [ -e "${i}" ];then rm -vf "${i}";fi
    done
    docker_cleanup
}

function cleanup() {
    for i in "${MS_DOCKERF_S0}" "${MS_DOCKERF_S1}" ;do
        if [ -e "${i}" ];then rm -vf "${i}";fi
    done
    docker_cleanup
}

if [ "x${THIS_AS_FUNCS}" = "x" ];then
    only_cleanup=""
    for i in $@;do
        if [ "x$i" = "x--cleanup" ];then
            only_cleanup="1"
        fi
    done
    cleanup
    if [ "x${only_cleanup}" != "x" ];then
        full_cleanup
        exit $?
    fi
    build_stage0
    ret="${?}"
    cleanup
    if [ "x${ret}" = "x0" ];then
        build_image
    fi
    ret="${?}"
    #cleanup
fi
exit ${ret}
# vim:set et sts=4 ts=4 tw=0:

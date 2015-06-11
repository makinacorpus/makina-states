#!/usr/bin/env bash
RED='\e[31;01m'
PURPLE='\e[35;01m'
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
cwd="$(cd "$(dirname "${0}")/.." && pwd)"
MS_OS="${MS_OS:-"ubuntu"}"
MS_OS_MIRROR="${MS_OS_MIRROR:-"http://mirror.ovh.net/ftp.ubuntu.com/"}"
DEFAULT_RELEASE=""
MS_COMMAND="${MS_COMMAND:-"/bin/systemd"}"
if [ "x${MS_OS}" = "xubuntu" ];then DEFAULT_RELEASE="vivid";fi
MS_OS_RELEASE="${MS_OS_RELEASE:-"${DEFAULT_RELEASE}"}"
MS_DOCKER_ARGS="${MS_DOCKER_ARGS:-""}"
MS_BASE="${MS_BASE:-"scratch"}"
MS_DATA_DIR="${MS_DATA_DIR:-"${cwd}/data"}"
MS_DOCKER_STAGE0="${MS_DOCKER_STAGE0:-"${cwd}/docker/stage0.sh"}"
MS_DOCKER_STAGE1="${MS_DOCKER_STAGE1:-"${cwd}/docker/stage1.sh"}"
MS_DOCKER_STAGE2="${MS_DOCKER_STAGE2:-"${cwd}/docker/stage2.sh"}"
MS_DOCKER_STAGE3="${MS_DOCKER_STAGE3:-"${cwd}/docker/stage3.sh"}"
MS_DOCKERFILE="${MS_DOCKERFILE:-"${cwd}/docker/Dockerfile.${MS_OS}.${MS_OS_RELEASE}"}"
MS_STAGE0_TAG="${MS_STAGE0_TAG:-"makinacorpus/makina-states-${MS_OS}-${MS_OS_RELEASE}-stage0:latest"}"
MS_GIT_BRANCH="${MS_GIT_BRANCH:-"stable"}"
MS_GIT_URL="${MS_GIT_URL:-"https://github.com/makinacorpus/makina-states.git"}"
MS_IMAGE="${MS_IMAGE:-"makinacorpus/makina-states-${MS_OS}-${MS_OS_RELEASE}"}"

echo;echo
yellow "-----------------------------------------------"
yellow "-   makina-states docker build system         -"
yellow "-----------------------------------------------"
yellow "-   STAGE 0  - BUIDING                        -"
yellow "-----------------------------------------------"
echo

# copy base boiler plate to the build directory
if [ ! -d "${MS_DATA_DIR}" ];then
    v_run mkdir -p "${MS_DATA_DIR}"
    die_in_error "${MS_IMAGE}: ${MS_DATA_DIR} datadir cant be created"
fi
mid="$(docker inspect -f "{{.Id}}" "${MS_STAGE0_TAG}" 2>/dev/null)"
if [ "x${?}" != "x0" ];then
    mid=""
fi
v_run docker build --rm -t "${MS_STAGE0_TAG}" -f "${MS_DOCKERFILE}" "${cwd}"
die_in_error "${MS_IMAGE}: stage0 didn't build correctly"
nmid="$(docker inspect -f "{{.Id}}" "${MS_STAGE0_TAG}" 2>/dev/null)"
if [ "x${mid}" != "x" ];then
    if [ "x${mid}" = "x${nmid}" ];then
        yellow "${MS_IMAGE}: stage0 already built"
    else
        docker rmi "${mid}"
        if [ "x${?}" != "x0" ];then
            yellow "${MS_IMAGE}: stage0 can't cleanup old image"
        else
            yellow "${MS_IMAGE}: stage0 cleaned up old image: ${mid}"
        fi
    fi
fi
purple "--------------------"
purple "- stage0 complete  -"
purple "--------------------"
v_run docker run --privileged -ti --rm \
 -e container="docker" \
 -e MS_BASE="${MS_BASE}" \
 -e MS_COMMAND="${MS_COMMAND}" \
 -e MS_GIT_BRANCH="${MS_GIT_BRANCH}" \
 -e MS_GIT_URL="${MS_GIT_URL}" \
 -e MS_IMAGE="${MS_IMAGE}" \
 -e MS_OS_MIRROR="${MS_OS_MIRROR}" \
 -e MS_OS="${MS_OS}" \
 -e MS_OS_RELEASE="${MS_OS_RELEASE}" \
 -e MS_OS_MIRROR="${MS_OS_MIRROR}" \
 -e MS_STAGE0_TAG="${MS_STAGE0_TAG}" \
 -v "${MS_DATA_DIR}":/docker_data \
 -v "${MS_DOCKERFILE}":/bootstrap_scripts/Dockerfile \
 -v "${cwd}/files/sbin/makinastates-snapshot.sh":/bootstrap_scripts/makinastates-snapshot.sh \
 -v "${cwd}/files/sbin/lxc-cleanup.sh":/bootstrap_scripts/lxc-cleanup.sh \
 -v "${MS_DOCKER_STAGE0}":/bootstrap_scripts/stage0.sh \
 -v "${MS_DOCKER_STAGE1}":/bootstrap_scripts/stage1.sh \
 -v "${MS_DOCKER_STAGE2}":/bootstrap_scripts/stage2.sh \
 -v "${MS_DOCKER_STAGE3}":/bootstrap_scripts/stage3.sh \
 -v /sys/fs:/sys/fs:ro \
 -v /usr/bin/docker:/usr/bin/docker:ro \
 -v /var/lib/docker:/var/lib/docker \
 -v /var/run/docker.sock:/var/run/docker.sock \
 -v /var/run/docker:/var/run/docker \
 ${MS_DOCKER_ARGS} "${@}" "${MS_STAGE0_TAG}" /bootstrap_scripts/stage1.sh
die_in_error "${MS_IMAGE}: Upper stages failed, see logs"
# vim:set et sts=4 ts=4 tw=80:

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
cwd="$(cd $(dirname "${0}") && pwd)"
MS_OS="${MS_OS:-"ubuntu"}"
MS_OS_MIRROR="${MS_OS_MIRROR:-"http://mirror.ovh.net/ftp.ubuntu.com/"}"
DEFAULT_RELEASE=""
if [ "x${MS_OS}" = "xubuntu" ];then DEFAULT_RELEASE="vivid";fi
MS_OS_RELEASE="${MS_OS_RELEASE:-"${DEFAULT_RELEASE}"}"
MS_DOCKER_ARGS="${MS_DOCKER_ARGS:-}"
MS_DATA_DIR="${MS_DATA_DIR:-${cwd}}"
MS_DOCKER_STAGE0="${0}"
MS_DOCKER_STAGE1="${MS_DOCKER_STAGE1:-"${cwd}/stage1.sh"}"
MS_DOCKER_STAGE2="${MS_DOCKER_STAGE2:-"${cwd}/stage2.sh"}"
MS_DOCKER_STAGE3="${MS_DOCKER_STAGE3:-"${cwd}/stage3.sh"}"
MS_DOCKERFILE="${MS_DOCKERFILE:-"Dockerfile.${MS_OS}.${MS_OS_RELEASE}"}"
MS_STAGE0_TAG="${MS_STAGE0_TAG:-"makinacorpus/makina-states-${MS_OS}-${MS_OS_RELEASE}-0"}"
MS_GIT_BRANCH="${MS_GIT_BRANCH:-"stable"}"
MS_GIT_URL="${MS_GIT_URL:-"https://github.com/makinacorpus/makina-states.git"}"
MS_IMAGE="${MS_IMAGE:-"makinacorpus/makina-states-${MS_OS}-${MS_OS_RELEASE}"}"
docker build -t "${STAGE0_TAG}" -f "${MS_DOCKERFILE}"
die_in_error "${MS_IMAGE}: stage0 didnt build"
docker run --privileged -ti --rm \
    -e MS_GIT_BRANCH="${MS_GIT_BRANCH}" \
    -e MS_GIT_URL="${MS_GIT_URL}" \
    -e MS_IMAGE="${MS_IMAGE}" \
    -e MS_OS_MIRROR="${MS_OS_MIRROR}" \
    -e MS_OS="${MS_OS_RELEASE}" \
    -e MS_OS_RELEASE="${MS_OS_RELEASE}" \
    -e MS_OS_RELEASE="${MS_OS_RELEASE}" \
    -e MS_STAGE0_TAG="${MS_STAGE0_TAG}" \
    -v "${MS_DATA_DIR}":/data \
    -v "${MS_DOCKERFILE}":/bootstrap_scripts/Dockerfile \
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
die_in_error "${MS_IMAGE}: upper stages failed, see logs"
# vim:set et sts=4 ts=4 tw=80:

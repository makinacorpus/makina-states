#!/usr/bin/env bash
# THIS SCRIPT CAN BE OVERRIDEN IN ANY MAKINA-STATES BASED IMAGES
# Copy/Edit it inside the overrides directory either:
#   - inside you image data directory, inside the image_roots/bootstrap_scripts
#   - inside your corpus based repository, inside the .salt folder

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

echo;echo
yellow "-----------------------------------------------"
yellow "-   makina-states docker build system         -"
yellow "-----------------------------------------------"
yellow "-   STAGE 0  - BUIDING                        -"
yellow "-----------------------------------------------"
echo
mid="$(docker inspect -f "{{.Id}}" "${MS_STAGE0_TAG}" 2>/dev/null)"
if [ "x${?}" != "x0" ];then
    mid=""
fi
if [ "x${MS_SKIP_STAGE0_BUILD}" = "x" ];then
    v_run docker build --rm \
        -t "${MS_STAGE0_TAG}" \
        -f "${MS_BOOTSTRAP_DIR}/Dockerfile.stage0" \
        "${cwd}"
    die_in_error "${MS_IMAGE}: stage0 didn't build correctly"
else
    yellow "${MS_IMAGE}: stage0 building is skipped, be sure that stage0 is available"
fi
nmid="$(docker inspect -f "{{.Id}}" "${MS_STAGE0_TAG}" 2>/dev/null)"
die_in_error "${MS_IMAGE}: stage0 can not be found"
if [ "x${mid}" != "x" ];then
    if [ "x${mid}" = "x${nmid}" ];then
        yellow "${MS_IMAGE}: stage0 found"
    else
        docker rmi -f "${mid}" \
            && yellow "${MS_IMAGE}: stage0 cleaned up old image: ${mid}"
        warn_in_error "${MS_IMAGE}: stage0 can't cleanup old image"
    fi
fi
echo
purple "--------------------"
purple "- stage0 complete  -"
purple "--------------------"
echo
v_run docker run \
 -e container="docker" \
 -e MS_BASE="${MS_BASE}" \
 -e MS_BASEIMAGE="${MS_BASEIMAGE}" \
 -e MS_COMMAND="${MS_COMMAND}" \
 -e MS_GIT_BRANCH="${MS_GIT_BRANCH}" \
 -e MS_GIT_URL="${MS_GIT_URL}" \
 -e MS_IMAGE="${MS_IMAGE}" \
 -e MS_OS_MIRROR="${MS_OS_MIRROR}" \
 -e MS_OS="${MS_OS}" \
 -e MS_OS_RELEASE="${MS_OS_RELEASE}" \
 -e MS_OS_MIRROR="${MS_OS_MIRROR}" \
 -e MS_DO_SNAPSHOT="${MS_DO_SNAPSHOT}" \
 -e MS_STAGE0_TAG="${MS_STAGE0_TAG}" \
 -e MS_STAGE1_NAME="${MS_STAGE1_NAME}" \
 -e MS_STAGE2_NAME="${MS_STAGE2_NAME}" \
 -e MS_IMAGE_CANDIDATE="${MS_IMAGE_CANDIDATE}" \
 -e MS_MAKINASTATES_BUILD_FORCE="${MS_MAKINASTATES_BUILD_FORCE}" \
 -v "${MS_DATA_DIR}":/docker/data \
 -v "${MS_DATA_DIR}/${MS_IMAGE}":/docker/image \
 -v "${MS_DATA_DIR}/${MS_IMAGE}/injected_volumes":/docker/injected_volumes \
 -v "${cwd}":/docker/makina-states \
 -v /sys/fs:/sys/fs:ro \
 -v /usr/bin/docker:/usr/bin/docker:ro \
 -v /var/lib/docker:/var/lib/docker \
 -v /var/run/docker:/var/run/docker \
 -v /var/run/docker.sock:/var/run/docker.sock \
 ${MS_DOCKER_ARGS} --privileged -ti --rm \
 --name=${MS_STAGE1_NAME} "${MS_STAGE0_TAG}"
die_in_error "${MS_IMAGE}: Upper stages failed, see logs"
purple "-----------------------------------------------------"
purple "- Build complete"
purple "- Check image tag: $(cyan ${MS_IMAGE_CANDIDATE})"
purple "-----------------------------------------------------"
# vim:set et sts=4 ts=4 tw=0:

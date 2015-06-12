#!/usr/bin/env bash
# THIS SCRIPT CAN BE OVERRIDEN IN ANY MAKINA-STATES BASED IMAGES
# REMOVE/EDIT THE ROLLOWING MARKER TO UNINDICATE THAT THIS IS A DEFAULT SCRIPT
# makina-states-default-stage-file

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
    v_run docker build --rm -t "${MS_STAGE0_TAG}" -f "${MS_DOCKERFILE}" "${cwd}"
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
        docker rmi "${mid}"\
            && yellow "${MS_IMAGE}: stage0 cleaned up old image: ${mid}"
        warn_in_error "${MS_IMAGE}: stage0 can't cleanup old image"
    fi
fi
echo
purple "--------------------"
purple "- stage0 complete  -"
purple "--------------------"
echo
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
 -e MS_STAGE1_NAME="${MS_STAGE1_NAME}" \
 -e MS_STAGE2_NAME="${MS_STAGE2_NAME}" \
 -e MS_BASEIMAGE="${MS_BASEIMAGE}" \
 -v "${MS_DATA_DIR}":/docker/data \
 -v "${MS_DATA_DIR}/${MS_IMAGE}/injected_volumes":/docker/injected_volumes \
 -v "${MS_DATA_DIR}/${MS_IMAGE}/injected_volumes":/injected_volumes \
 -v "${cwd}/.git":/makina-states.git \
 -v /sys/fs:/sys/fs:ro \
 -v /usr/bin/docker:/usr/bin/docker:ro \
 -v /var/lib/docker:/var/lib/docker \
 -v /var/run/docker:/var/run/docker \
 -v /var/run/docker.sock:/var/run/docker.sock \
 -v "${MS_DATA_DIR}/injected_volumes":/injected_volumes \
 -v "${cwd}/files/sbin/lxc-cleanup.sh":/injected_volumes/bootstrap_scripts/lxc-cleanup.sh \
 -v "${cwd}/files/sbin/makinastates-snapshot.sh":/injected_volumes/bootstrap_scripts/makinastates-snapshot.sh \
 ${MS_DOCKER_ARGS} "${@}" --name="${MS_STAGE1_NAME}" "${MS_STAGE0_TAG}"
die_in_error "${MS_IMAGE}: Upper stages failed, see logs"
# vim:set et sts=4 ts=4 tw=80:

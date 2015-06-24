#!/usr/bin/env bash
# THIS SCRIPT CAN BE OVERRIDEN IN ANY MAKINA-STATES BASED IMAGES
# Copy/Edit it inside the overrides directory either:
#   - inside you image data directory, inside the image_roots/bootstrap_scripts
#   - inside your corpus based repository, inside the .salt folder

RED='\e[31;01m'
CYAN='\e[36;01m'
YELLOW='\e[33;01m'
PURPLE='\e[33;01m'
GREEN='\e[32;01m'
NORMAL='\e[0m'

purple() { echo -e "${PURPLE}${@}${NORMAL}"; }
red() { echo -e "${RED}${@}${NORMAL}"; }
cyan() { echo -e "${CYAN}${@}${NORMAL}"; }
green() { echo -e "${GREEN}${@}${NORMAL}"; }
yellow() { echo -e "${YELLOW}${@}${NORMAL}"; }
die_in_error() { if [ "x${?}" != "x0" ];then red "${@}";exit 1;fi }
warn_in_error() { if [ "x${?}" != "x0" ];then yellow "WARNING: ${@}";fi }
v_run() { green "${@}"; "${@}"; }
v_die_run() { v_run "${@}"; die_in_error "command ${@} failed"; }
no_kill() { echo "Ignoring kill request"; }
breakpoint() {
    arg=$@
    touch /breakpoint
    echo "To attach the container"
    echo "docker exec -ti ${MS_STAGE2_NAME} bash"
    echo "To continue, exec in the container"
    echo "rm -f /breakpoint"
    while test -e /breakpoint;do
        sleep 5
    done
    if [ "x${arg}" != "x" ];then
        return ${arg}
    fi
}
echo;echo
yellow "-------------------------------------"
yellow "-   STAGE 2  - BUILDING             -"
yellow "-------------------------------------"
echo

# prerequisites
if which apt-get >/dev/null 2>&1;then
    apt-get update
    v_run apt-get install -y --force-yes git ca-certificates rsync acl patch
fi

# - Inject the wanted data inside the image
if [ -e /docker/injected_volumes/ ];then
    setfacl -R -bk /docker/injected_volumes
    v_run rsync -Aa /docker/injected_volumes/ /
fi

# - Save environment for subshell scripts & history
env > /bootstrap_scripts/stage2.env

# cleanup a bit the lxc if needed
if [ -f /bootstrap_scripts/lxc-cleanup.sh ];then
    v_run /bootstrap_scripts/lxc-cleanup.sh
fi

# When debugging commands, this can help to trap kill commands
# trap 'no_kill' 1 2 9

#breakpoint $?
# 1. Launch systemd
# apply system patch for running in containers as non pid1
# as without, systemd can lockup
if [ -e /lib/lsb/init-functions.d/40-systemd  ];then
    if ! grep -q makinacorpus_container_init /lib/lsb/init-functions.d/40-systemd;then
        v_die_run patch -Np2 < /docker/makina-states/files/lib/lsb/init-functions.d/40-systemd.patch
    fi
fi

wait_systemd() {
    systemdstarted=""
    for i in $(seq 240);do
        state=$(systemctl is-system-running)
        if [ "x${state}" = "xdegraded" ] || [ "x${state}" = "xrunning" ];then
            systemdstarted="1"
            break
        else
            sleep 1
        fi
    done
    if [ "x${systemdstarted}" = "x" ];then
        red "${MS_IMAGE}: systemd failed starting up";exit 1
    fi
}

restart_systemd_dbus() {
    # the systemd dir creation seems to make dbus work
    if [ $i -gt 5 ];then
        # dbus is flaky on trusty host / vivid container, this is an ugly workaround
        systemctl stop dbus
        sleep 0.5
        ps aux|grep dbus|awk '{print $2}'|xargs kill -9
        systemctl start dbus
        sleep 2
    fi
}

if echo "${MS_COMMAND}" | grep -q "systemd";then
    ( systemd --system& )
    sleep 2
    wait_systemd
fi
export DEBIAN_FRONTEND=noninteractive

# when debugging systemd boot, this make a breakpoint here.
# breakpoint $?
for i in /srv/pillar /srv/mastersalt-pillar /srv/projects;do
    if [ ! -d ${i} ];then mkdir ${i};fi
done

# We do not automatically trigger makina-states rebuild as it is
# an heavy and error prone process.
# We prefer to rely on those simple rules
#   - If we are a base makina-states image, rebuild
#   - If the installation seems broken, rebuild
if [ "x$(echo "${MS_IMAGE}" | sed -re "s/[^/]*\///g")" = "xmakina-states-${MS_OS}-${MS_OS_RELEASE}" ];then
    MS_MAKINASTATES_BUILD_FORCE="y"
else
    for pref in /srv/salt /salt/mastersalt;do
        for i in bin/salt bin/salt-call src/salt;do
            if [ ! -e ${pref}/${i} ];then MS_MAKINASTATES_BUILD_FORCE="y";fi
        done
    done
fi

# 2. Refresh makina-states code if needed
if [ "x${MS_MAKINASTATES_BUILD_FORCE}" = "x" ];then
    yellow "${MS_IMAGE}: makina-states integration is skipped, skipping makina-states install"
else
    for pref in /srv/salt /srv/mastersalt;do
        if [ ! -d ${pref} ];then mkdir -p ${pref};fi
        bs="${pref}/makina-states/_scripts/boot-salt.sh"
        if [ ! -e ${bs} ];then
            git clone /docker/makina-states/.git "${pref}/makina-states" &&\
                cd ${pref}/makina-states &&\
                git remote rm origin &&\
                warn_in_error \
                    "${MS_IMAGE}: problem while initing makina-states code (${pref})"
        fi
    done
    # setup mastersalt + salt highstates & masterless mode
    # breakpoint $?
    ${bs} -C -b "${MS_GIT_BRANCH}"  --mastersalt 127.0.0.1 -n dockercontainer\
        --local-mastersalt-mode masterless --local-salt-mode masterless
    # when debugging installation boot, this make a breakpoint here.
    breakpoint $?
    die_in_error "${MS_IMAGE}: failed installing makina-states"
fi
# if image root is a corpus based project, we push the code inside the image and
# initialise the corpus project
if [ -e "/docker/image/.git" ] && [ -e "/docker/data/.salt/PILLAR.sample" ];then
    commit=$(cd /docker/image && git log HEAD|head -n1|awk '{print $2}')
    if [ ! -e /srv/projects/app/project ];then
        salt-call --local mc_project.deploy app
        die_in_error "${MS_IMAGE}: project layout creation failure"
    fi &&\
        v_run cd /srv/projects/app/project &&\
        ( git remote rm app || /bin/true ) &&\
        git remote add app /docker/data/.git &&\
        git fetch --all &&\
        v_run git reset --hard "${commit}"
fi
echo
purple "--------------------"
purple "- stage2 complete  -"
purple "--------------------"
# 4. Run project installation, this is this script
#    which will be mostly configured by users
if [ -x /bootstrap_scripts/docker_build_stage3.sh ];then
    /bootstrap_scripts/docker_build_stage3.sh
    die_in_error "${MS_IMAGE}: Stage3 building failed"
fi
if [ "x${MS_DO_SNAPSHOT}" = "xyes" ] && [ -f /bootstrap_scripts/makinastates-snapshot.sh ];then
    /bootstrap_scripts/makinastates-snapshot.sh
fi
v_run getfacl -R / > /acls.txt || /bin/true
v_run touch /acls.restore
echo
purple "--------------------"
purple "- POSIX Acls saved -"
purple "--------------------"
echo
# END -- The common case is to tag back the image as a release candidate at the end
if docker inspect "${MS_IMAGE_CANDIDATE}" >/dev/null 2>&1;then
    docker rmi -f "${MS_IMAGE_CANDIDATE}"
fi
v_run docker commit -c "CMD ${MS_COMMAND}" "${MS_STAGE2_NAME}" "${MS_IMAGE_CANDIDATE}"
die_in_error "${MS_IMAGE_CANDIDATE} failed commit"
# vim:set et sts=4 ts=4 tw=0:

#!/usr/bin/env bash
OLD_MS_BRANCH="${MS_BRANCH:-stable}"
env
set -x
apt-get install xz-utils python rsync acl
set -e
./_scripts/install_prebuilt_makina_states.py --skip-salt
set +e
if [ -f /etc/makina-states/nodetype ];then
    rm -vf /etc/makina-states/nodetype
fi
sed -i -re "/makina-states.nodetypes.*: (true|false)/ d" /etc/*salt/grains
cd /srv/salt/makina-states
git fetch --all
git reset --hard remotes/origin/${MS_BRANCH} \
 || export MS_BRANCH="stable"
if [ "x${MS_BRANCH}" != "x${OLD_MS_BRANCH}" ];then
    git reset --hard remotes/origin/${MS_BRANCH}
fi
cd /srv/mastersalt/makina-states
git fetch --all
git reset --hard remotes/origin/${MS_BRANCH}
BOOTSALT_ARGS="${BOOTSALT_ARGS:-"-C -b ${MS_BRANCH}"}"
BOOTSALT_ARGS="${BOOTSALT_ARGS} --local-salt-mode masterless"
BOOTSALT_ARGS="${BOOTSALT_ARGS} --local-mastersalt-mode masterless"
BOOTSALT_ARGS="${BOOTSALT_ARGS} -n travis"
if ! ./_scripts/boot-salt.sh ${BOOTSALT_ARGS};then
    cat .bootlogs/*
    exit 1
fi
exit ${?}
# vim:set et sts=4 ts=4 tw=0:

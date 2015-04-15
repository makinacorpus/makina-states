#!/usr/bin/env bash
OLD_MS_BRANCH="${MS_BRANCH:-stable}"
env
set -x
apt-get install xz-utils python rsync acl
set -e
./_scripts/install_prebuilt_makina_states.py --skip-salt
set +e
cd /srv/mastersalt/makina-states
git fetch --all
git reset --hard remotes/origin/${MS_BRANCH} \
 || export MS_BRANCH="stable"
if [ "x${MS_BRANCH}" != "x${OLD_MS_BRANCH}" ];then
    git reset --hard remotes/origin/${MS_BRANCH}
fi
if ! ./_scripts/boot-salt.sh -b ${MS_BRANCH};then
    cat .bootlogs/*
    exit 1
fi
exit ${?}
# vim:set et sts=4 ts=4 tw=0:

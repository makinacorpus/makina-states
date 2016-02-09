#!/usr/bin/env bash
CWD="${PWD}"
REPO="/srv/ms.git"
OLD_MS_BRANCH="${TRAVIS_COMMIT:-v2}"
MS_BRANCH="$(git log|head -n1|awk '{print $2}')"
CMS_BRANCH="changeset:${MS_BRANCH}"
BOOTSALT_ARGS=""
BOOTSALT_ARGS="${BOOTSALT_ARGS} -C -b ${CMS_BRANCH}"
BOOTSALT_ARGS="${BOOTSALT_ARGS} -n travis"
set -x
env
apt-get install xz-utils python rsync acl
if [ -f /etc/makina-states/nodetype ];then
    rm -vf /etc/makina-states/nodetype
fi
sed -i -re "/makina-states.nodetypes.*: (true|false)/ d" /etc/*salt/grains
rm -f .git/shallow
git clone --mirror --bare . "${REPO}"
i="/srv/makina-states"
mkdir -p $i
git clone "${REPO}" "${i}"
git reset --hard ${MS_BRANCH}
if ! ./_scripts/boot-salt.sh ${BOOTSALT_ARGS};then
    exit 1
fi
# be sure to let travis be sudoer, in case
echo "travis ALL=NOPASSWD: ALL">>/etc/sudoers
exit ${?}
# vim:set et sts=4 ts=4 tw=0:

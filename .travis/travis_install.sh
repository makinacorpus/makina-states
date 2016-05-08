#!/usr/bin/env bash
CWD="${PWD}"
REPO="/srv/ms.git"
OLD_MS_BRANCH="${TRAVIS_COMMIT:-v2}"
MS_BRANCH="$(git log|head -n1|awk '{print $2}')"
CMS_BRANCH="changeset:${MS_BRANCH}"
BOOTSALT_ARGS="-C -b ${CMS_BRANCH} -n travis --highstates"
set -x
env
apt-get install -y --force-yes xz-utils python rsync acl
rm -f .git/shallow
git clone --mirror --bare . "${REPO}"
i="/srv/makina-states"
git clone "${REPO}" "${i}"
cd "${i}"
git reset --hard "${MS_BRANCH}"
if ! ./_scripts/boot-salt.sh ${BOOTSALT_ARGS};then
    exit 1
fi
. venv/bin/activate
if ! pip install -r requirements/dev.txt;then
    exit 1
fi
# be sure to let travis be sudoer, in case
echo "travis ALL=NOPASSWD: ALL">>/etc/sudoers
exit ${?}
# vim:set et sts=4 ts=4 tw=0:

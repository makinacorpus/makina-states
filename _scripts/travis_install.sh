#!/usr/bin/env bash
CWD="${PWD}"
REPO="/srv/ms.git"
OLD_MS_BRANCH="${TRAVIS_COMMIT:-stable}"
MS_BRANCH="$(git log|head -n1|awk '{print $2}')"
CMS_BRANCH="changeset:${MS_BRANCH}"
BOOTSALT_ARGS=""
BOOTSALT_ARGS="${BOOTSALT_ARGS} -C -b ${CMS_BRANCH}"
BOOTSALT_ARGS="${BOOTSALT_ARGS} --local-salt-mode masterless"
BOOTSALT_ARGS="${BOOTSALT_ARGS} --local-mastersalt-mode masterless"
BOOTSALT_ARGS="${BOOTSALT_ARGS} -n travis"
set -x
env
apt-get install xz-utils python rsync acl
if !  ./_scripts/install_prebuilt_makina_states.py --skip-salt;then
    exit 1
fi
if [ -f /etc/makina-states/nodetype ];then
    rm -vf /etc/makina-states/nodetype
fi
sed -i -re "/makina-states.nodetypes.*: (true|false)/ d" /etc/*salt/grains
rm -f .git/shallow
git clone --mirror --bare . "${REPO}"
cd /srv/salt/makina-states
git remote rm travis || /bin/true
git remote add travis "${REPO}"
git fetch --all
git reset --hard ${MS_BRANCH}
cd /srv/mastersalt/makina-states
git remote rm travis || /bin/true
git remote add travis "${REPO}"
git fetch --all
git reset --hard ${MS_BRANCH}
if ! ./_scripts/boot-salt.sh ${BOOTSALT_ARGS};then
    cat /etc/shorewall/params
    cat /etc/shorewall/rules
    shorewall check
    for i in $(ls .bootlogs/* -1t | head -n 5);do
        cat "${i}"
    done
    exit 1
fi
cat /etc/sudoers
# be sure to let travis be sudoer, in case
echo "travis ALL=NOPASSWD: ALL">>/etc/sudoers
for i in mastersalt salt;do
    cd /srv/${i}/makina-states
    bin/pip install -r requirements/dev.txt
done
exit ${?}
# vim:set et sts=4 ts=4 tw=0:

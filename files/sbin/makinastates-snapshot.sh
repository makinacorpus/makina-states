#!/usr/bin/env bash

set -e
if [ "x${DEBUG}" != "x" ];then set -x;fi
if [ "x$1" = "xstop" ];then
    for i in salt-master salt-minion mastersalt-master mastersalt-minion;do
        service "${i}" stop
    done
fi
is_docker=""
from_systemd="y"
for i in ${@};do
    if [ "x${i}" = "xsystemd" ];then
        from_systemd="y"
    fi
done
for i in /.dockerinit /.dockerenv;do
    if [ -f "${i}" ];then
        is_docker="1"
        break
    fi
done
if [ "x${is_docker}" != "x" ];then
    if [ "x$(grep -q "system.slice/docker-" /proc/1/cgroup 2>/dev/null;echo ${?})" = "x0" ];then
        is_docker="1"
    fi
fi

REMOVE="
/tmp/.saltcloud
/root/.cache
/etc/makina-states/nodetype
/home/*/.cache
/etc/systemd/system/multi-user.target.wants/mastersalt-minion.service
/etc/systemd/system/multi-user.target.wants/mastersalt-master.service
/etc/systemd/system/multi-user.target.wants/salt-minion.service
/etc/systemd/system/multi-user.target.wants/salt-master.service
"
if [ "x${is_docker}" != "x" ];then
    set +e
    find /srv/projects/*/archives \
     -mindepth 1 -maxdepth 1 -type d|while read i;do
        rm -rf "${i}" || /bin/true
    done
    REMOVE="${REMOVE}
/salt-venv/mastersalt/lib/python2.7/site-packages/libcloud/test/compute/fixtures
/salt-venv/salt/lib/python2.7/site-packages/libcloud/test/compute/fixtures
"
fi
set -e
# directories to empty out or files to wipe content from
WIPE="
/etc/mastersalt/makina-states/
/etc/salt/makina-states/
/etc/makina-states/*.pack
/etc/makina-states/*.yaml

/etc/mastersalt/makina-states
/etc/salt/makina-states
/usr/local/share/ca-certificates/

/tmp

/etc/ssh/ssh_host*key
/etc/ssh/ssh_host*pub

/etc/ssl/apache
/etc/ssl/cloud
/etc/ssl/nginx

/srv/salt/makina-states/.bootlogs/
/srv/mastersalt/makina-states/.bootlogs/

/var/log/unattended-upgrades/
/var/log/*.1
/var/log/*.0
/var/log/*.gz
"
# files to delete
FILE_REMOVE="
/srv/mastersalt-pillar/
/srv/pillar/
/var/cache/apt/archives/
/var/lib/apt/lists
/etc/salt/pki
/etc/mastersalt/pki
"
FILE_WIPE="
/var/log
"
# salt cache is relying on semi hardlinks, deleting files from their orig
# just delete/create the caches is sufficient
TO_RECREATE="
/var/cache/salt/minion
/var/cache/salt/salt-minion
/var/cache/salt/salt-master
/var/cache/mastersalt/mastersalt-master
/var/cache/mastersalt/mastersalt-minion
/var/cache/mastersalt/minion
/var/cache/mastersalt/master-master
"
# we already have clean checkouts, now, we do not upgrade
# if [ "x${is_docker}" != "x" ];then
#     /srv/mastersalt/makina-states/_scripts/boot-salt.sh -C -s -S --only-pack || /bin/true
# fi

echo "${TO_RECREATE}" | while read i;do
    if [ "x${i}" != "x" ];then
        if [ ! -h "${i}" ];then
            if [ -f "${i}" ];then
                rm -fv "${i}" || /bin/true
                touch "${i}" || /bin/true
            elif [ -d "${i}" ];then
                rm -rv "${i}" || /bin/true
                mkdir -v "${i}" || /bin/true
            fi
        fi
    fi
done
for i in ${REMOVE};do
    if [ -d "${i}" ];then rm -vrf "${i}" || /bin/true;fi
    if [ -h "${i}" ] || [ -f "${i}" ];then rm -vf "${i}" || /bin/true;fi
done
echo "${WIPE}" | while read i;do
    if [ "x${i}" != "x" ];then
        ls -1 ${i} 2>/dev/null| while read k;do
            if [ -h "${k}" ];then
                rm -fv "${k}" || /bin/true
            elif [ -f "${k}" ];then
                find "${k}" -type f | while read fic;do rm -fv "${fic}" || /bin/true;done
            elif [ -d "${k}" ];then
                find "${k}" -mindepth 1 -maxdepth 1 -type d | while read j;do
                    if [ ! -h "${j}" ];then
                        rm -vrf "${j}" || /bin/true
                    else
                        rm -vf "${j}" || /bin/true
                    fi
                done
                find "${i}" -mindepth 1 -maxdepth 1 -type f | while read j;do
                    rm -vf "${j}" || /bin/true
                done
            fi
        done
    fi
done
# special case, log directories must be in place, but log resets
echo "${FILE_REMOVE}" | while read i;do
    if [ "x${i}" != "x" ];then
        find "${i}" -type f | while read f;do rm -f "${f}" || /bin/true;done
    fi
done
echo "${FILE_WIPE}" | while read i;do
    if [ "x${i}" != "x" ];then
        find "${i}" -type f | while read f;do echo > "${f}" || /bin/true;done
    fi
done
find /srv/pillar /srv/mastersalt-pillar /etc/*salt/minion* -type f|while read i
do
    sed -i -re "s/master:.*/master: 0.0.0.1/g" "$i" || /bin/true
    sed -i -re "s/id:.*/id: localminion/g" "$i" || /bin/true
done
find /etc/shorewall/rules -type f|while read i
do
    sed -i -re "s/ACCEPT.? +net:?.*fw +-/ACCEPT net fw/g" "$i" || /bin/true
done
for i in salt mastersalt;do
    j="/etc/${i}/grains"
    if [ -e "${j}" ];then
        sed -i -re "/makina-states.nodetypes.*: (true|false)/ d" "${j}" || /bin/true
    fi
done
find / -name .ssh | while read i;do
echo $i
    if [ -d "${i}" ];then
        pushd "${i}" 1>/dev/null 2>&1
        for i in config authorized_keys authorized_keys2;do
            if [ -f "${i}" ];then echo >"${i}";fi
        done
        ls -1 known_hosts id_* 2>/dev/null| while read f;do rm -vf "${f}";done
        popd 1>/dev/null 2>&1
    fi
done
find /root /home /var -name .bash_history -or -name .viminfo\
    | while read fic;do echo >"${fic}";done
find /etc/init/*salt* | grep -v override | while read fic
    do
        echo manual > ${fic//.conf}.override
    done
for i in\
    /etc/makina-states/local_salt_mode \
    /etc/makina-states/local_mastersalt_mode \
;do
    if [ -e "${i}" ];then echo masterless > "${i}";fi
done
if [ -e /etc/.git ] && [ -e /usr/bin/etckeeper ];then
    rm -rf /etc/.git
    # save space in image
    if [ "x${is_docker}" != "x" ];then
        etckeeper init || /bin/true
        cd /etc
        git config user.name "name"
        git config user.email "a@b.com"
        etckeeper commit "init" || /bin/true
    fi

fi
if which getfacl 1>/dev/null 2>/dev/null;then
    getfacl -R / > /acls.txt || /bin/true
    if [ -e /acls.txt ];then
        xz -f -z -9e /acls.txt || /bin/true
    fi
fi
# deactivate some crons (leave only refresh one only on non docker-env)
if [ "x${is_docker}" != "x" ];then
    sed -i -re "s/(.*boot-salt\.sh.*--refresh-modules.*)/#\1/g" /etc/cron.d/*salt* || /bin/true
fi
sed -i -re "s/(.*boot-salt\.sh.*--check-alive.*)/#\1/g" /etc/cron.d/*salt* || /bin/true
sed -i -re "s/(.*boot-salt\.sh.*--cleanup.*)/#\1/g" /etc/cron.d/*salt* || /bin/true
sed -i -re "s/(.*boot-salt\.sh.*--restart-masters.*)/#\1/g" /etc/cron.d/*salt* || /bin/true
sed -i -re "s/(.*boot-salt\.sh.*--restart-minions.*)/#\1/g" /etc/cron.d/*salt* || /bin/true

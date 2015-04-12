#!/usr/bin/env bash

set -e
if [ "x${DEBUG}" != "x" ];then set -x;fi
if [ "x$1" = "xstop" ];then
    for i in salt-master salt-minion mastersalt-master mastersalt-minion;do
        service "${i}" stop
    done
fi

REMOVE="
/tmp/.saltcloud
"

WIPE="
/usr/local/share/ca-certificates/

/var/cache/salt/salt-master
/var/cache/salt/salt-minion

/var/cache/mastersalt/master-master
/var/cache/mastersalt/mastersalt-minion

/etc/salt/pki/master/minions
/etc/mastersalt/pki/master/minions

/etc/mastersalt/pki/minion
/etc/salt/pki/minion
/tmp

/etc/salt/pki/master/master.pem
/etc/salt/pki/master/master.pub

/etc/mastersalt/pki/master/master.pem
/etc/mastersalt/pki/master/master.pub

/etc/ssh/ssh_host*key
/etc/ssh/ssh_host*pub

/etc/ssl/apache
/etc/ssl/cloud
/etc/ssl/nginx

/srv/mastersalt-pillar/top.sls
/srv/pillar/top.sls

/srv/salt/makina-states/.bootlogs/*
/srv/mastersalt/makina-states/.bootlogs/*

/var/log/unattended-upgrades/*
/var/log/*.1
/var/log/*.0
/var/log/*.gz
"
FILE_REMOVE="
/var/cache/apt/archives/
/var/lib/apt/lists
"
FILE_WIPE="
/var/log
"

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
done
find /etc/shorewall/rules -type f|while read i
do
    sed -i -re "s/ACCEPT.? +net:?.*fw +-/ACCEPT net fw/g" "$i" || /bin/true
done
find /root /home /var -name .bash_history | while read fic;do echo >"${fic}";done
find /etc/init/*salt* | grep -v override | while read fic
    do
        echo manual > ${fic//.conf}.override
    done
if which getfacl 1>/dev/null 2>/dev/null;then
    getfacl -R / > /acls.txt || /bin/true
fi

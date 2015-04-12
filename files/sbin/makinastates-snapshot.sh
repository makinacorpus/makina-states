#!/usr/bin/env bash
set -e
if [ "x${DEBUG}" != "x" ] ;then
    set -x
fi
if [ "x$1" = "xstop" ];then
    for i in salt-master salt-minion mastersalt-master mastersalt-minion;do
        service $i stop
    done
fi
if [ -e /tmp/.saltcloud ];then
    rm -rfv /tmp/.saltcloud
fi
for i in /var/cache/salt/{salt-master,salt-minion} /var/cache/mastersalt/{master-master,mastersalt-minion} /etc/.git;do
    if [ -e "${i}" ];then
        rm -rfv "${i}"/*
    fi
done
for i in /tmp;do
    if [ -e "${i}" ];then
        cd "${i}" && find|while read f;do
            if [ "x${f}" != "x." ];then rm -rfv "${f}";fi
        done
    fi
done
find /etc/*salt/pki/master/minions*/*\
    /etc/*salt/pki/master/master.{pem,pub}\
    /etc/*salt/pki/minion/*\
    /srv/pillar/top.sls\
    /srv/mastersalt-pillar/top.sls\
    /srv/*salt/makina-states/.bootlogs/*\
    /var/log/upstart/*\
    /var/log/*.log\
    /var/log/mastersalt/*.gz\
    /var/log/salt/*.gz\
    /etc/ssh/ssh_host_*{key,pub}\
    /var/log/mastersalt/mastersalt-master\
    /var/log/mastersalt/mastersalt-minion\
    /var/log/salt/salt-master\
    /var/log/salt/salt-minion\
    | while read fic;do rm -fv "${fic}" || /bin/true ;done
if [ -e /var/lib/apt/lists ];then
    find /var/lib/apt/lists -type f -delete || /bin/true
fi
find /srv -name .git|while read f
do
    cd "${f}/.."
    gmarker=".git/curgitpackid"
    if [ ! -f $gmarker ];then
        echo 1 > $gmarker
    fi
    gitpackid=$(cat $gmarker)
    if [ "x$((${gitpackid}%10))" = "x0" ];then
        git prune || /bin/true
        git gc --aggressive || /bin/true
        echo $((${gitpackid}+1)) > $gmarker
    fi
done
find /srv/pillar /srv/mastersalt-pillar /etc/*salt/minion* -type f|while read i
do
    sed -i -re "s/master:.*/master: 0.0.0.1/g" "$i"
done
find /etc/shorewall/rules -type f|while read i
do
    sed -i -re "s/ACCEPT.? +net:?.*fw +-/ACCEPT net fw/g" "$i"
done
find / -name .bash_history | while read fic;do echo >"${fic}";done
find /etc/init/*salt* |grep -v override| while read fic
    do
        echo manual > ${fic//.conf}.override
    done
find /var/cache/apt/archives -name "*deb" -type f -delete 2>/dev/null || /bin/true
if [ -e /etc/ssl/cloud ];then
    find /etc/ssl/cloud -type -f -delete 2>/dev/null || /bin/true
fi

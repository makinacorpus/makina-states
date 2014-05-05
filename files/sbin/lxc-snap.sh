#!/usr/bin/env bash
if [ "x$1" = "xstop" ];then
for i in salt-master salt-minion mastersalt-master mastersalt-minion;do
    service $i stop
done
fi
rm -rfv /tmp/.saltcloud
find /etc/*salt/pki/master/minions*/*\
     /etc/*salt/pki/master/master.{pem,pub}\
     /etc/*salt/pki/minion/*\
     /srv/pillar/top.sls\
     /srv/mastersalt-pillar/top.sls\
     /srv/*salt/makina-states/.bootlogs/*\
     /var/log/upstart/*\
     /var/log/*.log\
  | while read fic;do rm -fv "${fic}";done
sed -i -e "s/master:.*/master: 0.0.0.1/g" $(find /etc/*salt/minion* -type f)
find / -name .bash_history | while read fic;do echo >"${fic}";done
find /etc/init/*salt* |grep -v override\
  | while read fic;do 
    echo manual > ${fic//.conf}.override
done

#!/usr/bin/env bash
mark="/root/.salt_lxc_core_packages"
ms="/srv/salt/makina-states"
ntp_postinst="$ms/files/root/debbuild/ntp_postinst"
if [ ! -e "$mark" ];then
    if [ ! -e "/root/debbuild" ];then mkdir -pv /root/debbuild;fi &&\
    cd /root/debbuild &&\
    for i in resolvconf fuse ntp;do
      mkdir -p $i && cd $i &&\
      apt-get download -y $i &&\
      dpkg-deb -X $i*deb build &&\
      dpkg-deb -e $i*deb build/DEBIAN && \
      rm *deb && cd .. ;\
    done &&\
    cp "$ntp_postinst" /root/debbuild/ntp/build/DEBIAN/postinst &&\
    echo "#!/bin/bash"   >/root/debbuild/resolvconf/build/DEBIAN/postinst &&\
    echo "exit 0"       >>/root/debbuild/resolvconf/build/DEBIAN/postinst &&\
    echo ""             >>/root/debbuild/resolvconf/build/DEBIAN/postinst &&\
    echo "#!/bin/bash"   >/root/debbuild/fuse/build/DEBIAN/postinst &&\
    echo "#exit 0"      >>/root/debbuild/fuse/build/DEBIAN/postinst &&\
    echo ""             >>/root/debbuild/fuse/build/DEBIAN/postinst &&\
    for i in fuse resolvconf ntp;do
      cd /root/debbuild/$i/build &&\
      dpkg-deb -b . /root/debbuild/$i.deb;\
    done
    apt-get install -y $(dpkg-deb -I /root/debbuild/ntp.deb |egrep "^\s*Depends:"|sed -re "s/\([^\)]+\)//g" -e "s/,//g" -e "s/Depends://g") &&\
    for i in fuse resolvconf ntp;do\
      dpkg -i /root/debbuild/$i.deb&&\
      echo $i hold | dpkg --set-selections;\
    done && touch "$mark"
fi
exit $?
# vim:set et sts=4 ts=4 tw=80:

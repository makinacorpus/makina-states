#!/usr/bin/env bash
gmark="/root/.salt_lxc_core_packages"
ms="/srv/salt/makina-states"
ntp_postinst="$ms/files/root/debbuild/ntp_postinst"
apt_update=""
#for i in resolvconf fuse ntp;do
for i in fuse ntp;do
    mark="${gmark}_${i}"
    if [ ! -e "$mark" ];then
        if [ ! -e "/root/debbuild" ];then mkdir -pv /root/debbuild;fi
        cd /root/debbuild
        mkdir -p "${i}"
        cd "${i}"
        rm -f ${i}*deb
        set -e
        if [ "x${apt_update}" = "x" ];then
            apt-get update
            apt_update="1"
        fi
        apt-get download -y $i
        dpkg-deb -X ${i}*deb build
        dpkg-deb -e ${i}*deb build/DEBIAN
        rm -f *deb
        cd ..
        if [ "x$i" = "xntp" ];then
            cp "$ntp_postinst"    /root/debbuild/ntp/build/DEBIAN/postinst
        fi
        if echo "${i}"|egrep -q "resolvconf|fuse";then
            echo "#!/bin/bash" >"/root/debbuild/${i}/build/DEBIAN/postinst"
            echo "exit 0"     >>"/root/debbuild/${i}/build/DEBIAN/postinst"
            echo ""           >>"/root/debbuild/${i}/build/DEBIAN/postinst"
        fi
        cd "/root/debbuild/${i}/build"
        dpkg-deb -b . "/root/debbuild/${i}.deb"
        apt-get install -y $(dpkg-deb -I /root/debbuild/${i}.deb \
            |egrep "^\s*Depends:"\
            |sed -re "s/\([^\)]+\)//g" -e "s/,//g" -e "s/Depends://g"\
            |sed -re "s/[|]//g" -e "s/udev|makedev//g")
        dpkg -i /root/debbuild/${i}.deb
        echo ${i} hold | dpkg --set-selections
        touch "${mark}"
        set +e
    fi
done
exit ${?}
# vim:set et sts=4 ts=4 tw=80:

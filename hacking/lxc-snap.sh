#!/usr/bin/env bash
set -x
set -e
lxc="${1}"
if [ "x${lxc}" = "x" ];then
    echo no lxc
    exit 1
fi
cd /var/lib/lxc
test -e "${lxc}"
rsync -aAv "${lxc}"/ "${lxc}".snap/ \
    --delete-excluded \
    --delete-excluded \
    --exclude="${lxc}.tbz2" \
    --exclude=rootfs/srv/projects/*/data/snapshots \
    --exclude="rootfs/tmp/*" \
    --exclude="rootfs/var/log/*/*gz" \
    --exclude="rootfs/var/log/*gz" \
    --exclude=rootfs/etc/ssl/cloud/ \
    --exclude=rootfs/etc/ssl/nginx
chroot "${lxc}.snap/rootfs" /sbin/makinastates-snapshot.sh
chroot "${lxc}.snap/rootfs" getfacl -R / >${lxc}.snap/rootfs/acls.txt
cd "${lxc}".snap/
getfacl -R . >acls.txt
tar cjvf  "../${lxc}.tbz2" .

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
    --exclude=data/snapshots --exclude="rootfs/tmp/*" \
    --exclude=data/snapshots --exclude="var/log/*/*gz" \
    --delete-excluded --exclude="var/log/*gz" --exclude=etc/ssl/cloud/ --exclude=etc/ssl/nginx
chroot "${lxc}.snap/rootfs" /sbin/makinastates-snapshot.sh
chroot "${lxc}.snap/rootfs" getfacl -R / >${lxc}.snap/rootfs/acls.txt
cd "${lxc}".snap/
getfacl -R . >acls.txt
tar cjvf  "../${lxc}.tbz2" .

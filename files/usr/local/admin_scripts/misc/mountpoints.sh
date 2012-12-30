#!/usr/bin/env bash

mountpoints="var/cache/salt var/lib/docker var/lib/lxc"
mountpoints="var/lib/docker var/lib/lxc"
for i in $mountpoints;do
 orig="/srv/mountpoints/${i//\//_}"
 dest="/$i"
 mkdir -p "$orig" "$dest"
 rsync -azv "$dest/" "$orig/"
 echo "$orig $dest none bind 0 0">>/etc/fstab
 mount ${orig}
done

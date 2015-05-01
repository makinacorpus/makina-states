#!/usr/bin/env bash
# {% set docker = salt['mc_cloud_vm.vt_settings']('docker') %}
if [ -f /etc/default/docker ]; then
    . /etc/default/docker
fi 
cgroupfs_mount() {
    # see also https://github.com/tianon/cgroupfs-mount/blob/master/cgroupfs-mount
    if grep -v '^#' /etc/fstab | grep -q cgroup \
        || [ ! -e /proc/cgroups ] \
        || [ ! -d /sys/fs/cgroup ]; then
        return
    fi
    if ! mountpoint -q /sys/fs/cgroup; then
        mount -t tmpfs -o uid=0,gid=0,mode=0755 cgroup /sys/fs/cgroup
    fi
    (
        cd /sys/fs/cgroup
        for sys in $(awk '!/^#/ { if ($4 == 1) print $1 }' /proc/cgroups); do
            mkdir -p ${sys}
            if ! mountpoint -q ${sys}; then
                if ! mount -n -t cgroup -o ${sys} cgroup ${sys}; then
                    rmdir ${sys} || true
                fi
            fi
        done
    )
}
cgroupfs_mount
exec "${DOCKER}" ${DOCKER_OPTS}
# vim:set et sts=4 ts=4 tw=80:

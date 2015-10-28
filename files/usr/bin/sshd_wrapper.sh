#!/usr/bin/env bash
PATH="${PATH}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export PATH
for i in ${SSHD} $(which sshd) /usr/sbin/sshd;do
    if [ -x "${i}" ];then
        SSHD=${i}
        break
    fi
done
set -x
if [ ! -f /etc/ssh/ssh_host_rsa_key ];then
    ssh-keygen -f /etc/ssh/ssh_host_rsa_key -N '' -t rsa -b 4096 || /bin/true
fi
if [ ! -f /etc/ssh/ssh_host_dsa_key ];then
    ssh-keygen -f /etc/ssh/ssh_host_dsa_key -N '' -t dsa -b 1024 || /bin/true
fi
if [ ! -f /etc/ssh/ssh_host_ed25519_key ];then
    ssh-keygen -f /etc/ssh/ssh_host_ed25519_key -N '' -t ed25519 || /bin/true
fi
if [ ! -f /etc/ssh/ssh_host_ecdsa_key ];then
    ssh-keygen -f /etc/ssh/ssh_host_ecdsa_key   -N '' -t  ecdsa  || /bin/true
fi
exec "${SSHD}" "${@}"
# vim:set et sts=4 ts=4 tw=80:

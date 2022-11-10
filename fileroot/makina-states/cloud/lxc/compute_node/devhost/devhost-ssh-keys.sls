{# specific install rules on devhost for lxc managment #}
include:
  {# lxc may not be installed directly on the cloud controller ! #}
  - makina-states.services.virt.lxc.devhost
  - makina-states.nodetypes.vagrantvm-ssh-keys
  - makina-states.cloud.generic.hooks

cloud-lxc-devhost-symdir:
  file.directory:
    - name: /srv/lxc
    - makedirs: true
{# copy user ssh keys for pull/push inside containers #}
cloud-lxc-devhost-sync-sshs:
  file.managed:
    - name: /sbin/devhost-install-lxc-keys.sh
    - source : ""
    - contents: |
                #!/usr/bin/env bash
                /sbin/devhost-installkeys.sh;
                ls -d /var/lib/lxc/*/rootfs/root/ /var/lib/lxc/*/rootfs/home/*/ /var/lib/lxc/*/rootfs/home/users/*/ /var/lib/lxc/*/delta0/root/ /var/lib/lxc/*/delta0/home/*/ /var/lib/lxc/*/delta0/home/users/*/ 2>/dev/null|while read homedir 2>/dev/null;do
                    user="$(basename ${homedir})";
                    if [ -e "${homedir}/.ssh" ];then
                      rsync -av "/root/.ssh/" "${homedir}/.ssh/" --exclude=authorized_keys --exclude=authorized_keys2;
                      chmod -Rf 700 "${homedir}/.ssh/";
                      chown -Rf "${user}:${user}" "${homedir}/.ssh/";
                    fi;
                done;
                /sbin/lxc-devhostmount.sh mount
    - user: root
    - mode: 755
    - require_in:
      - cmd: cloud-lxc-devhost-sync-sshs
  cmd.run:
    - name: /sbin/devhost-install-lxc-keys.sh
    - user: root
    - watch:
      - mc_proxy: lxc-post-conf
      - mc_proxy: cloud-generic-final

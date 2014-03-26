{# specific install rules on devhost for lxc managment #}
include:
  {# lxc may not be installed directly on the cloud controller ! #}
  - makina-states.cloud.generic.hooks.common

cloud-lxc-devhost-symdir:
  file.directory:
    - name: /srv/lxc
    - makedirs: true

cloud-lxc-devhost-refresh-symlinks:
  cmd.run:
    - name: |
            cd /srv/lxc && rm * && for i in $(find /var/lib/lxc/ -mindepth 1 -maxdepth 1 -type d 2>/dev/null);do
              ln -sf ../..${i}/rootfs $(basename ${i});
              if [ -e ../..${i}/delta0 ];then ln -sf ../..${i}/delta0 $(basename ${i});fi;
            done
    - watch:
      - file: cloud-lxc-devhost-symdir
      - mc_proxy: cloud-generic-final

